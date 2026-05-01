import re
from typing import Generator, Tuple
from .llm_client import OllamaClient
from .context_manager import ContextManager
from .tools import get_tool_registry
from .prompt import get_system_message

class AgentOrchestrator:
    """
    The main execution loop for the Gemma-e4b agent.
    Manages the ReAct loop, parses tool calls, and handles self-correction.
    """
    def __init__(self, model_name: str = "gemma4:e4b"):
        self.llm_client = OllamaClient(model=model_name)
        # Initialize ContextManager with the client so it can perform summarization
        self.context_manager = ContextManager(max_tokens=8192, threshold_pct=0.8, llm_client=self.llm_client)
        self.tool_registry = get_tool_registry()
        
        # Inject the immutable System Prompt
        self.context_manager.add_message(get_system_message())

    def parse_tool_call(self, text: str) -> str:
        """Extracts the JSON block from the model's response."""
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            return match.group(1)
        return None

    def run_task(self, user_prompt: str) -> Generator[Tuple[str, str], None, None]:
        """
        Executes the autonomous ReAct loop.
        Yields tuples of (event_type, data) so the UI can render updates live.
        """
        # 1. Add the initial user request
        self.context_manager.add_message({"role": "user", "content": user_prompt})
        
        step_count = 0
        max_steps = 25 # Absolute safeguard to prevent infinite loops

        while step_count < max_steps:
            step_count += 1
            yield ("status", f"Thinking (Step {step_count})...")
            
            full_response = ""
            # Stream the model's response
            for chunk in self.llm_client.stream_chat(self.context_manager.messages):
                full_response += chunk
                yield ("stream", chunk)
                
            # 2. Store the complete assistant response in memory
            self.context_manager.add_message({"role": "assistant", "content": full_response})
            
            # 3. Parse for a tool call
            json_str = self.parse_tool_call(full_response)
            
            if json_str:
                yield ("status", "Executing Tool...")
                # 4. Execute the tool
                tool_result = self.tool_registry.execute(json_str)
                
                # 5. Check for the stopping condition
                if tool_result.startswith("TASK_COMPLETE:"):
                    yield ("complete", tool_result.replace("TASK_COMPLETE:", "").strip())
                    break
                    
                # 6. Feed the observation back to the model
                observation_msg = f"Observation:\n{tool_result}"
                self.context_manager.add_message({"role": "user", "content": observation_msg})
                yield ("observation", tool_result)
                
            else:
                # Self-Correction: The model failed to output a proper JSON tool call
                yield ("status", "Format Error. Prompting self-correction...")
                error_msg = (
                    "Observation: No valid JSON tool call found. You must use a tool to proceed, "
                    "or use the 'task_complete' tool if you are finished. Ensure your JSON is wrapped in ```json ``` tags."
                )
                self.context_manager.add_message({"role": "user", "content": error_msg})
                yield ("observation", error_msg)
                
        if step_count >= max_steps:
            yield ("error", "Agent reached maximum step limit (25) and was forcefully halted.")