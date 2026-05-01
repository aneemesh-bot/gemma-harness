import re
from typing import List, Dict
from transformers import AutoTokenizer

class ContextManager:
    """
    Manages the conversation history to ensure it stays within the VRAM token limits.
    Implements sliding-window summarization and <|think|> block pruning.
    """
    def __init__(self, max_tokens: int = 8192, threshold_pct: float = 0.8, llm_client=None):
        self.max_tokens = max_tokens
        self.threshold = int(self.max_tokens * threshold_pct)
        self.messages: List[Dict[str, str]] = []
        self.llm_client = llm_client
        
        # Load the tokenizer to accurately count tokens
        # Note: If you do not have a HuggingFace token set up, this will fall back to an estimation.
        try:
            self.tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b")
        except Exception as e:
            print(f"[Warning] Could not load Gemma tokenizer (Requires HuggingFace login). Using approximate token counting. Error: {e}")
            self.tokenizer = None

    def count_tokens(self, text: str) -> int:
        """Calculates token length of a given text."""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        # Fallback approximation: ~4 characters per token
        return len(text) // 4

    def get_total_tokens(self) -> int:
        """Returns the current token count of the entire message history."""
        return sum(self.count_tokens(msg["content"]) for msg in self.messages)

    def add_message(self, message: Dict[str, str]):
        """Adds a message to the history and triggers compression if the threshold is breached."""
        self.messages.append(message)
        current_tokens = self.get_total_tokens()
        
        if current_tokens > self.threshold:
            self._compress_context()

    def _compress_context(self):
        """Executes the two-stage compression pipeline."""
        # Step A: Structural Pruning
        self._prune_think_blocks()
        
        # Check if pruning was enough to drop below the threshold
        if self.get_total_tokens() > self.threshold:
            # Step B & C: Summarization and Reassembly
            self._summarize_history()

    def _prune_think_blocks(self):
        """Removes all internal reasoning blocks from past assistant messages."""
        for msg in self.messages:
            if msg["role"] == "assistant":
                # Regex to match and remove <|think|> ... </|think|> blocks across multiple lines
                pruned_content = re.sub(
                    r'<\|?think\|?>.*?</\|?think\|?>', 
                    '[Thinking block pruned for memory]', 
                    msg["content"], 
                    flags=re.DOTALL
                )
                msg["content"] = pruned_content

    def _summarize_history(self):
        """Partitions the context, summarizes the older messages, and reassembles the window."""
        if not self.llm_client:
            print("[Warning] No LLM client provided to ContextManager. Skipping summarization.")
            return

        # 1. Partition the history
        system_msgs = [m for m in self.messages if m["role"] == "system"]
        other_msgs = [m for m in self.messages if m["role"] != "system"]
        
        # Keep the most recent 3 turns (Present) untouched so the agent doesn't lose its current train of thought
        if len(other_msgs) <= 4:
            return # Not enough history to summarize
            
        past_msgs = other_msgs[:-3]
        present_msgs = other_msgs[-3:]
        
        # 2. Build the background summarization prompt
        summary_prompt = (
            "Summarize the following past actions and findings into a dense, bulleted list. "
            "Focus only on files modified, tests run, and bugs discovered. Omit code snippets:\n\n"
        )
        for m in past_msgs:
            summary_prompt += f"{m['role'].upper()}:\n{m['content']}\n\n"
            
        # 3. Call the LLM to generate the summary
        summary_response = ""
        for chunk in self.llm_client.stream_chat([{"role": "user", "content": summary_prompt}]):
            summary_response += chunk
            
        # 4. Reassemble the context window
        new_messages = system_msgs.copy()
        new_messages.append({
            "role": "system", 
            "content": f"[SYSTEM: Previous context summary:\n{summary_response.strip()}]"
        })
        new_messages.extend(present_msgs)
        
        self.messages = new_messages