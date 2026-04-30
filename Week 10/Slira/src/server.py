import os
import re
import uuid
from fastapi import FastAPI, Request
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from langgraph_sdk import get_client
from datetime import datetime

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

    # Grab the IDs we need to look up the thread
    thread_ts = event.get("thread_ts")
    message_ts = event.get("ts")
    channel_id = event.get("channel")
    
    thread_id_base = thread_ts if thread_ts else message_ts
    thread_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(thread_id_base)))

    # --- NEW: FETCH THREAD CONTEXT ---
    full_prompt = text
    if thread_ts:
        try:
            replies = await slack_app.client.conversations_replies(
                channel=channel_id,
                ts=thread_ts
            )
            
            # --- NEW: 14-DAY CALENDAR CHEAT SHEET ---
            today = datetime.now()
            history_text = "--- SYSTEM CALENDAR ---\n"
            for i in range(14):
                day = today + timedelta(days=i)
                if i == 0:
                    history_text += f"Today: {day.strftime('%A, %Y-%m-%d')}\n"
                elif i == 1:
                    history_text += f"Tomorrow: {day.strftime('%A, %Y-%m-%d')}\n"
                else:
                    history_text += f"In {i} days: {day.strftime('%A, %Y-%m-%d')}\n"
            history_text += "\n--- PREVIOUS THREAD CONTEXT ---\n"
            
            for msg in replies.get("messages", []):
                if msg.get("ts") != message_ts and not msg.get("bot_id"):
                    msg_text = _clean_text(msg.get("text", ""))
                    history_text += f"- {msg_text}\n"
            
            history_text += f"\n--- USER COMMAND ---\n{text}"
            full_prompt = history_text
            
        except Exception as e:
            print(f"Failed to fetch thread history: {e}")

    try:
        try:
            await langgraph_client.threads.get(thread_id=thread_uuid)
        except Exception:
            await langgraph_client.threads.create(thread_id=thread_uuid)
        
        # Pass the newly enriched 'full_prompt' to the AI
        await langgraph_client.runs.wait(
            thread_id=thread_uuid,
            assistant_id=assistant_id,
            input={
                "messages": [{"role": "user", "content": full_prompt}]
            }
        )

        state = await langgraph_client.threads.get_state(thread_id=thread_uuid)
        messages = state["values"].get("messages", [])
        
        ai_messages = [m for m in messages if m.get("type") == "ai" or m.get("role") == "assistant"]
        
        if ai_messages:
            last_message = ai_messages[-1]
            response_text = last_message.get("content", "I processed that, but have no text response.")
            
            if response_text.strip():
                await say(text=response_text, thread_ts=thread_id_base)

    except Exception as e:
        print(f"Error processing message: {e}")
        await say(text="Sorry, I ran into an error processing your request.", thread_ts=thread_id_base)

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