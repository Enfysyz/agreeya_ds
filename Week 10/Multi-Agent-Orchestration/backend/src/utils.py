import json
import logging

def extract_json(response_content: any, agent_name: str) -> dict:
    if isinstance(response_content, dict):
        return response_content
    try:
        return json.loads(response_content)
    except Exception as e:
        logging.error(f"[{agent_name}] JSON extraction failed: {e}")
        return {"error": f"Failed to extract valid data from {type(response_content)}"}
