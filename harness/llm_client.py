import json
import requests
from typing import List, Dict, Generator

class OllamaClient:
    """
    A lightweight wrapper for interacting with the local Ollama REST API.
    """
    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "gemma4:e4b"):
        self.base_url = base_url
        self.model = model
        self.chat_endpoint = f"{self.base_url}/api/chat"

    def stream_chat(self, messages: List[Dict[str, str]], options: Dict = None) -> Generator[str, None, None]:
        """
        Sends a list of messages to the Ollama chat API and yields the response chunks.
        
        Args:
            messages: A list of dicts, e.g., [{"role": "user", "content": "Hello!"}]
            options: Optional dictionary for Ollama parameters (e.g., {"num_ctx": 8192, "temperature": 1.0})
            
        Yields:
            String chunks of the model's generated response.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }
        
        # Inject context limits and generation parameters if provided
        if options:
            payload["options"] = options

        try:
            with requests.post(self.chat_endpoint, json=payload, stream=True) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line.decode('utf-8'))
                        
                        # Extract the streamed token/chunk
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
                            
                        # Stop yielding if Ollama signals the generation is complete
                        if data.get("done"):
                            break
                            
        except requests.exceptions.RequestException as e:
            # Yield an error string so the orchestrator can catch it and gracefully halt
            yield f"\n[LLM_ERROR: Failed to communicate with Ollama API: {str(e)}]"

# --- Verification Block (For isolated testing) ---
if __name__ == "__main__":
    # To test this module directly, run: python -m harness.llm_client
    # Note: Replace 'gemma:2b' with your specific local e4b model tag if different.
    client = OllamaClient(model="gemma4:e4b") 
    test_messages = [
        {"role": "system", "content": "You are a helpful AI."},
        {"role": "user", "content": "Say 'Hello World' and nothing else."}
    ]
    
    print("Testing Ollama connection...\nResponse: ", end="")
    for chunk in client.stream_chat(test_messages):
        print(chunk, end="", flush=True)
    print("\n\nTest complete.")