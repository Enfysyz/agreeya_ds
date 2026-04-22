import json
import requests

def test_agent():
    url = "http://localhost:8000/api/research"
    payload = {"topic": "Tourist spots in Los Angeles"}
    
    print(f"Connecting to {url} via standard HTTP POST...")
    
    try:
        # stream=True keeps the HTTP connection open to listen for yields
        with requests.post(url, json=payload, stream=True) as response:
            response.raise_for_status()
            print("Connected! Listening to SSE stream...\n")
            
            # Iterate through the chunks as they are yielded by the backend
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    
                    # We only care about the 'data: ' lines from the SSE format
                    if decoded_line.startswith("data: "):
                        json_str = decoded_line[len("data: "):]
                        data = json.loads(json_str)
                        
                        if data["type"] == "log":
                            url_info = f" ({data['url']})" if "url" in data else ""
                            print(f"[AGENT LOG]: {data['message']}{url_info}")
                            
                        elif data["type"] == "complete":
                            print("\n" + "="*50)
                            print("[FINAL REPORT SYNTHESIZED]")
                            print("="*50)
                            print(data["result"])
                            
                        elif data["type"] == "error":
                            print(f"\n[ERROR]: {data['message']}")
                            
    except requests.exceptions.ConnectionError:
        print("Could not connect. Is the Docker container running?")

if __name__ == "__main__":
    test_agent()