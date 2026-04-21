from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from agent import ResearchAgent

app = FastAPI(title="Deep Research AI Agent")

@app.websocket("/ws/research")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Wait for the frontend to send the research topic/keywords
        data = await websocket.receive_json()
        topic = data.get("topic")
        
        if not topic:
            await websocket.send_json({"type": "error", "message": "No topic provided."})
            return

        # Initialize and run the agent
        agent = ResearchAgent(websocket=websocket)
        await agent.run_research(topic)

    except WebSocketDisconnect:
        print("Frontend disconnected.")
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})