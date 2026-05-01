# Install Ollama model
```bash
docker exec -it ollama_slira ollama pull llama3.1
```

# Ngrok Setup
## Get URL
```bash
ngrok http 8000
```

## Update Slack Config
- Go to https://api.slack.com/apps and choose your app
- Change link under `Event Subscriptions` (eg. https<nolink>://a1b2-c3d4.ngrok-free.app/events/slack)

# Test Jira connection
```bash
docker-compose exec app python -c "from src.tools import jira_client; print('Connected Projects:', [p.key for p in jira_client.projects()])"
```

# Slira: The Slack-to-Jira AI Agent

Slira is a "Chat-to-Action" AI agent powered by LangGraph, Llama 3.1, and FastAPI. It lives in your Slack workspace and acts as an intelligent, conversational bridge to your Jira instance. Instead of clicking through Jira boards, users can simply ask Slira to create tickets, move statuses, or generate detailed audit logs of recent activity using natural language.

## Features & Capabilities

Slira maintains conversational memory within Slack threads, meaning you can have ongoing, contextual discussions about specific tickets without repeating yourself.

The agent is equipped with the following tools, which can be triggered using natural language in Slack:

### 1. Ticket Management

> **Human-in-the-Loop (HITL):**  
> All ticket creation actions follow a confirmation step. Slira first prepares a draft based on your input or conversation context and asks for approval before creating the ticket in Jira. Users can review, edit, or cancel the action.

* **Create Tickets:** Slira can extract project keys, summaries, and descriptions from your chat to instantly draft new Jira issues.

  * *Example:* `@Slira Create a bug in the KAN project titled 'Login API Failing' with the description 'The endpoint is returning a 500 error.'`

* **Slack Thread → Ticket Creation:** When a discussion in a Slack thread evolves into actionable work, Slira can automatically generate a Jira ticket from the entire conversation.

  * *Example:* `@Slira create a ticket for this in KAN`

* **Move Tickets:** Seamlessly transition tickets across your board.

  * *Example:* `@Slira Move KAN-123 to In Progress.`

### 2. Personal Productivity

* **Task Lookup:** Ask the bot to pull your personal agenda based on dynamic timeframes.

  * *Example:* `@Slira What tasks do I have due today? Are any overdue?`
* **Personal Audit Log (Daily Summary):** Generates a formatted standup report by analyzing the Jira changelog to see exactly what tickets you touched, updated, or moved in the last 24 hours.

  * *Example:* `@Slira Give me my daily status summary. What did I do today?`

### 3. Team Visibility

* **Team Activity Stream:** Pulls a 24-hour audit log of all updates across the engineering team, showing who moved what. This can be run globally or filtered by a specific project.

  * *Example:* `@Slira What has the team been working on in the last 24 hours?`
  * *Example:* `@Slira Show me the recent activity for the DEV project.`

---

## Tech Stack

* **Orchestration:** LangGraph & Langchain
* **LLM:** Ollama (Llama 3.1 8B running locally)
* **Server:** FastAPI (Python) & Uvicorn
* **Integrations:** Slack Bolt Framework & Jira Python API
* **Deployment:** Docker & Docker Compose

---

## First-Time Setup & Installation

### Prerequisites

Before you begin, ensure you have the following installed on your local machine:

* **Docker & Docker Compose**
* **Ngrok** (for tunneling Slack events to your local server)
* **Ollama** (with the `llama3.1` model pulled)

### 1. Configure Environment Variables

Create a `.env` file in the root directory of the project and populate it with the following required credentials:

```env
# --- Slack Configuration ---
# Found in the Slack API Dashboard under "OAuth & Permissions" -> "Bot User OAuth Token"
SLACK_BOT_TOKEN=xoxb-your-bot-token
# Found in the Slack API Dashboard under "Basic Information" -> "App Credentials"
SLACK_SIGNING_SECRET=your_signing_secret

# --- Jira Configuration ---
# Your base Jira URL (no trailing slash)
JIRA_SERVER_URL=https://your-workspace.atlassian.net
# The exact email address you use to log into Jira
JIRA_EMAIL=your-email@domain.com
# Generate an API Token from your Atlassian Account Security settings
JIRA_API_TOKEN=your_long_api_token_here

# --- LangGraph / LLM Configuration ---
OLLAMA_BASE_URL=http://host.docker.internal:11434
LANGGRAPH_ASSISTANT_ID=jira_agent
```

### 2. Start the Application

Build and start the application using Docker Compose. This will spin up the FastAPI server and install all necessary Python dependencies.

```bash
docker-compose up --build -d
```

Install the Ollama model

```bash
docker exec -it ollama_slira ollama pull llama3.1
```

*(Note: To view real-time logs and see the AI's internal thought process, run `docker-compose logs -f app`)*

### 3. Expose the Local Server to Slack

Because the server is running locally on port `8000`, Slack needs a public URL to send events to. Use Ngrok to create a secure tunnel:

```bash
ngrok http 8000
```

### 4. Configure Slack Event Subscriptions

1. Copy the secure `https` forwarding URL provided by Ngrok (e.g., `https://a1b2.ngrok-free.app`).
2. Go to your [Slack API Dashboard](https://api.slack.com/apps), select your app, and navigate to **Event Subscriptions**.
3. Paste the Ngrok URL into the **Request URL** field, appending `/events/slack` to the end:

   * *Example:* `https://a1b2.ngrok-free.app/events/slack`
4. Wait for the green **Verified** checkmark, scroll to the bottom, and click **Save Changes**.

*(If you are on the free tier of Ngrok, your URL will change every time you restart Ngrok. You must update the Slack dashboard with the new URL whenever this happens).*

---

## How Memory Works

Slira uses Slack `thread_ts` timestamps to generate unique, deterministic UUIDs for LangGraph.

* If you **reply in a thread**, the bot accesses its short-term memory and remembers previous tickets and context.
* If you send a **new message in the channel**, the bot starts with a fresh, blank state.


