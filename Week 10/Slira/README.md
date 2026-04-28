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
