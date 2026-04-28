import os
import re
import uuid  # <-- Add this import
from fastapi import FastAPI, Request
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from langgraph_sdk import get_client

# 1. Initialize the Slack App
slack_app = AsyncApp(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# 2. Initialize the LangGraph SDK Client
langgraph_client = get_client(url="http://localhost:8000")
assistant_id = os.environ.get("LANGGRAPH_ASSISTANT_ID", "jira_agent")

def _clean_text(text: str) -> str:
    """Removes the @BotName mention from the raw Slack text so the AI just reads the prompt."""
    return re.sub(r'<@U[A-Z0-9]+>', '', text).strip()

# 3. Listen for mentions and direct messages
@slack_app.event("app_mention")
@slack_app.event("message")
async def handle_slack_message(event, say):
    if event.get("bot_id"):
        return

    text = _clean_text(event.get("text", ""))
    if not text:
        return

    # Get the Slack timestamp
    thread_ts = event.get("thread_ts", event.get("ts"))
    
    # Convert the Slack timestamp into a deterministic UUID for LangGraph
    thread_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(thread_ts)))

    try:
        # Create a thread in LangGraph using the UUID
        try:
            await langgraph_client.threads.get(thread_id=thread_uuid)
        except Exception:
            await langgraph_client.threads.create(thread_id=thread_uuid)
        
        # Trigger the LangGraph agent run
        await langgraph_client.runs.wait(
            thread_id=thread_uuid,
            assistant_id=assistant_id,
            input={
                "messages": [{"role": "user", "content": text}]
            }
        )

        # Retrieve the final state
        state = await langgraph_client.threads.get_state(thread_id=thread_uuid)
        messages = state["values"].get("messages", [])
        
        if messages:
            last_message = messages[-1]
            response_text = last_message.get("content", "I processed that, but have no text response.")
            
            # Send the response back using the original Slack timestamp
            await say(text=response_text, thread_ts=thread_ts)

    except Exception as e:
        print(f"Error processing message: {e}")
        await say(text="Sorry, I ran into an error processing your request.", thread_ts=thread_ts)


# 4. Mount the Slack app to FastAPI
app = FastAPI()
slack_handler = AsyncSlackRequestHandler(slack_app)

@app.post("/events/slack")
async def slack_events(req: Request):
    return await slack_handler.handle(req)