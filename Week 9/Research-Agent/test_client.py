import asyncio
import websockets
import json

async def test_agent():
    uri = "ws://localhost:8000/ws/research"
    
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Sending research topic...")
            
            # Send the research topic to the backend
            request_data = {"topic": "Latest breakthroughs in solid-state batteries 2024"}
            await websocket.send(json.dumps(request_data))
            
            # Listen for the streaming logs and the final result
            while True:
                try:
                    response = await websocket.recv()
                    data = json.loads(response)
                    
                    if data["type"] == "log":
                        url_info = f" ({data['url']})" if "url" in data else ""
                        print(f"[AGENT LOG]: {data['message']}{url_info}")
                        
                    elif data["type"] == "complete":
                        print("\n" + "="*50)
                        print("[FINAL REPORT SYNTHESIZED]")
                        print("="*50)
                        print(data["result"])
                        break
                        
                    elif data["type"] == "error":
                        print(f"\n[ERROR]: {data['message']}")
                        break
                        
                except websockets.exceptions.ConnectionClosed:
                    print("\nConnection closed by the server.")
                    break
    except ConnectionRefusedError:
        print("Could not connect. Is the Docker container running?")

if __name__ == "__main__":
    asyncio.run(test_agent())