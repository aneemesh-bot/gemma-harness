import pytest
from harness.context_manager import ContextManager

class MockLLMClient:
    """A dummy client that yields a fake summary without hitting the Ollama API."""
    def stream_chat(self, messages, options=None):
        yield "Mocked summary of past events."

def test_token_counting_fallback():
    """Tests the ~4 chars per token fallback math."""
    manager = ContextManager()
    manager.tokenizer = None  # Force the fallback approximation
    text = "123456789012345678901234" # 24 chars
    
    # 24 chars // 4 = 6 tokens
    assert manager.count_tokens(text) == 6

def test_prune_think_blocks():
    """Verifies that reasoning blocks are successfully stripped to save memory."""
    manager = ContextManager(max_tokens=8192)
    
    bloated_message = {
        "role": "assistant",
        "content": "<|think|>\nThis reasoning is taking up too much space and should be pruned.\n</|think|>\n```json\n{\"tool\": \"test\"}\n```"
    }
    
    manager.add_message(bloated_message)
    manager._prune_think_blocks()
    
    pruned_content = manager.messages[0]["content"]
    assert "This reasoning is taking up too much space" not in pruned_content
    assert "[Thinking block pruned for memory]" in pruned_content
    assert "```json" in pruned_content

def test_summarization_pipeline():
    """Forces an Out-Of-Memory condition to ensure the partition and summary triggers."""
    mock_client = MockLLMClient()
    # Set a tiny max_tokens so it triggers almost immediately
    manager = ContextManager(max_tokens=100, threshold_pct=0.5, llm_client=mock_client)
    manager.tokenizer = None # Use approximation for predictable testing
    
    manager.add_message({"role": "system", "content": "You are a bot."})
    
    # Flood the context to breach the 50 token threshold
    for i in range(5):
        manager.add_message({"role": "user", "content": f"Bloat message {i} " * 5})
        
    manager._compress_context()
    
    # Verify the structure: System Prompt -> Summary Prompt -> Remaining recent history
    roles = [m["role"] for m in manager.messages]
    assert roles[0] == "system"
    assert roles[1] == "system" 
    
    # Verify our mock summary was injected
    assert "Mocked summary of past events." in manager.messages[1]["content"]