import json
from typing import Dict, Callable

class ToolRegistry:
    """
    Parses LLM JSON output and routes it to the correct sandboxed tool function.
    """
    def __init__(self):
        self.tools: Dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        self.tools[name] = func

    def execute(self, json_str: str) -> str:
        try:
            # Clean up markdown formatting if the model wrapped it in ```json ... ```
            clean_json = json_str.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
                
            data = json.loads(clean_json.strip())
            tool_name = data.get("tool")
            
            if not tool_name:
                return "Error: Tool name not provided in JSON."
            
            if tool_name not in self.tools:
                return f"Error: Tool '{tool_name}' is not recognized."
            
            # Extract arguments by removing the 'tool' key
            kwargs = {k: v for k, v in data.items() if k != "tool"}
            
            # Execute tool safely
            result = self.tools[tool_name](**kwargs)
            return str(result)
            
        except json.JSONDecodeError:
            return "Error: Invalid JSON format. Please ensure your output is valid JSON."
        except TypeError as e:
            return f"Error: Invalid arguments provided for the tool. {str(e)}"
        except Exception as e:
            return f"Error executing tool: {str(e)}"