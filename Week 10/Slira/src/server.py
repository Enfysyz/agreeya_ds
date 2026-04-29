import os
import re
import uuid
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
    """Removes the @BotName mention from the raw Slack text."""
    return re.sub(r'<@U[A-Z0-9]+>', '', text).strip()

async def run_langgraph_agent(event, say):
    text = _clean_text(event.get("text", ""))
    if not text:
        return

    thread_ts = event.get("thread_ts", event.get("ts"))
    thread_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(thread_ts)))

    try:
        try:
            await langgraph_client.threads.get(thread_id=thread_uuid)
        except Exception:
            await langgraph_client.threads.create(thread_id=thread_uuid)
        
        await langgraph_client.runs.wait(
            thread_id=thread_uuid,
            assistant_id=assistant_id,
            input={
                "messages": [{"role": "user", "content": text}]
            }
        )

        state = await langgraph_client.threads.get_state(thread_id=thread_uuid)
        messages = state["values"].get("messages", [])
        
        # FILTER: Only grab messages where the type is 'ai' (ignores human messages and tool outputs)
        ai_messages = [m for m in messages if m.get("type") == "ai" or m.get("role") == "assistant"]
        
        if ai_messages:
            # Safely get the very last AI response
            last_message = ai_messages[-1]
            response_text = last_message.get("content", "I processed that, but have no text response.")
            
            # Prevent sending blank messages if the AI only called a tool without text
            if response_text.strip():
                await say(text=response_text, thread_ts=thread_ts)

    except Exception as e:
        print(f"Error processing message: {e}")
        await say(text="Sorry, I ran into an error processing your request.", thread_ts=thread_ts)

# 4. Separated Listeners to prevent Double-Triggering
@slack_app.event("app_mention")
async def handle_mentions(event, say):
    await run_langgraph_agent(event, say)

@slack_app.event("message")
async def handle_messages(event, say):
    """Triggers ONLY on direct messages (DMs)."""
    # Channel type 'im' ensures we ignore channel messages here
    if event.get("channel_type") == "im" and not event.get("bot_id"):
        await run_langgraph_agent(event, say)

app = FastAPI()
slack_handler = AsyncSlackRequestHandler(slack_app)

@app.post("/events/slack")
async def slack_events(req: Request):
    return await slack_handler.handle(req)