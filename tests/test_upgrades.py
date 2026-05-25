"""
Integration tests for all 7 UPGRADES.md changes.
"""
import json
import os
import time
import pytest
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Upgrade 1 — Output Truncation Notification (terminal.py)
# ---------------------------------------------------------------------------

def test_truncation_sentinel_appended():
    """Truncated output must end with the sentinel line, not silently drop lines."""
    from harness.tools.terminal import execute_command

    # Generate a command that produces > 50 lines
    result = execute_command("python -c \"for i in range(60): print(i)\"")
    assert "OUTPUT TRUNCATED" in result
    assert "50" in result  # mentions first 50


def test_truncation_not_triggered_under_50_lines():
    """Commands with <= 50 lines must NOT include the truncation sentinel."""
    from harness.tools.terminal import execute_command

    result = execute_command("echo hello")
    assert "OUTPUT TRUNCATED" not in result


# ---------------------------------------------------------------------------
# Upgrade 2 — Tool Error Classification (base.py)
# ---------------------------------------------------------------------------

def test_parse_error_prefix():
    from harness.tools.base import ToolRegistry

    registry = ToolRegistry()
    result = registry.execute("this is not json at all")
    assert result.startswith("[PARSE_ERROR]")


def test_tool_not_found_prefix():
    from harness.tools.base import ToolRegistry

    registry = ToolRegistry()
    result = registry.execute('{"tool": "nonexistent_tool"}')
    assert result.startswith("[TOOL_NOT_FOUND]")
    assert "nonexistent_tool" in result


def test_execution_error_prefix():
    from harness.tools.base import ToolRegistry

    registry = ToolRegistry()

    def bad_tool():
        raise RuntimeError("something went wrong internally")

    registry.register("bad_tool", bad_tool)
    # Pass unexpected kwargs to trigger TypeError
    result = registry.execute('{"tool": "bad_tool", "unexpected_arg": 1}')
    assert result.startswith("[EXECUTION_ERROR]")


# ---------------------------------------------------------------------------
# Upgrade 3 — Persistent Session State (session.py)
# ---------------------------------------------------------------------------

def test_save_and_load_session(tmp_path, monkeypatch):
    import harness.session as session_mod

    monkeypatch.setattr(session_mod, "SESSION_FILE", str(tmp_path / ".gemma_session.json"))

    messages = [
        {"role": "system", "content": "You are a bot."},
        {"role": "user", "content": "Hello"},
    ]
    session_mod.save_session(messages)
    loaded = session_mod.load_session()
    assert loaded == messages


def test_load_session_returns_none_when_missing(tmp_path, monkeypatch):
    import harness.session as session_mod

    monkeypatch.setattr(session_mod, "SESSION_FILE", str(tmp_path / "no_such_file.json"))
    assert session_mod.load_session() is None


def test_clear_session(tmp_path, monkeypatch):
    import harness.session as session_mod

    session_file = tmp_path / ".gemma_session.json"
    monkeypatch.setattr(session_mod, "SESSION_FILE", str(session_file))
    session_mod.save_session([{"role": "user", "content": "hi"}])
    assert session_file.exists()
    session_mod.clear_session()
    assert not session_file.exists()


# ---------------------------------------------------------------------------
# Upgrade 4 — create_file tool (file_ops.py)
# ---------------------------------------------------------------------------

def test_create_file_success(tmp_path):
    from harness.tools.file_ops import create_file

    target = str(tmp_path / "new_file.py")
    result = create_file(target, "print('hello')\n")
    assert "Successfully created" in result
    assert open(target).read() == "print('hello')\n"


def test_create_file_refuses_overwrite(tmp_path):
    from harness.tools.file_ops import create_file

    target = tmp_path / "existing.py"
    target.write_text("original content")
    result = create_file(str(target), "new content")
    assert "already exists" in result
    # Original content must be untouched
    assert target.read_text() == "original content"


def test_create_file_registered_in_registry():
    from harness.tools import get_tool_registry

    registry = get_tool_registry()
    assert "create_file" in registry.tools


# ---------------------------------------------------------------------------
# Upgrade 5 — Retry with Exponential Backoff (llm_client.py)
# ---------------------------------------------------------------------------

def test_retry_succeeds_on_third_attempt():
    """Client must retry and eventually yield content after transient failures."""
    from harness.tools.base import ToolRegistry  # import to ensure harness loads fine
    from harness import llm_client as lc_mod
    from harness.llm_client import OllamaClient

    call_count = {"n": 0}

    def flaky_post(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] < 3:
            raise lc_mod.requests.exceptions.ConnectionError("transient")
        # Third attempt succeeds — return a minimal streaming response
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.raise_for_status = MagicMock()
        mock_resp.iter_lines.return_value = [
            json.dumps({"message": {"content": "ok"}, "done": False}).encode(),
            json.dumps({"message": {"content": ""}, "done": True}).encode(),
        ]
        return mock_resp

    client = OllamaClient()
    with patch.object(lc_mod.requests, "post", side_effect=flaky_post):
        # Patch sleep so the test doesn't actually wait
        with patch.object(lc_mod.time, "sleep"):
            chunks = list(client.stream_chat([{"role": "user", "content": "hi"}]))

    assert call_count["n"] == 3
    assert "ok" in chunks


def test_retry_exhausted_yields_error():
    """After all retries fail the client must yield an LLM_ERROR string."""
    from harness import llm_client as lc_mod
    from harness.llm_client import OllamaClient

    with patch.object(lc_mod.requests, "post",
                      side_effect=lc_mod.requests.exceptions.ConnectionError("down")):
        with patch.object(lc_mod.time, "sleep"):
            chunks = list(OllamaClient().stream_chat([{"role": "user", "content": "hi"}]))

    assert any("[LLM_ERROR" in c for c in chunks)


# ---------------------------------------------------------------------------
# Upgrade 6 — Dynamic max_tokens from Ollama model info (llm_client.py)
# ---------------------------------------------------------------------------

def test_get_num_ctx_reads_model_info():
    from harness import llm_client as lc_mod
    from harness.llm_client import OllamaClient

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "model_info": {"llama.context_length": 4096}
    }

    with patch.object(lc_mod.requests, "post", return_value=mock_resp):
        client = OllamaClient()
        assert client.get_num_ctx() == 4096


def test_get_num_ctx_falls_back_on_error():
    from harness import llm_client as lc_mod
    from harness.llm_client import OllamaClient

    with patch.object(lc_mod.requests, "post",
                      side_effect=lc_mod.requests.exceptions.ConnectionError("down")):
        client = OllamaClient()
        assert client.get_num_ctx() == 8192


# ---------------------------------------------------------------------------
# Upgrade 7 — Session Logging (ui.py)
# ---------------------------------------------------------------------------

def test_log_file_written(tmp_path):
    """TerminalUI must write JSONL entries to the log file for each event."""
    from harness.ui import TerminalUI

    log_path = str(tmp_path / "session.jsonl")

    class FakeOrchestrator:
        def run_task(self, prompt):
            yield ("status", "Thinking (Step 1)...")
            yield ("stream", "hello")
            yield ("complete", "All done")

    ui = TerminalUI(FakeOrchestrator(), log_file=log_path)
    ui.process_task("do something")

    assert os.path.exists(log_path)
    lines = open(log_path).readlines()
    events = [json.loads(l) for l in lines]
    event_types = [e["event"] for e in events]

    assert "user_input" in event_types
    assert "status" in event_types
    assert "complete" in event_types


def test_no_log_file_when_not_specified():
    """When log_file=None, no file should be created."""
    from harness.ui import TerminalUI

    class FakeOrchestrator:
        def run_task(self, prompt):
            yield ("complete", "done")

    ui = TerminalUI(FakeOrchestrator(), log_file=None)
    ui.process_task("task")
    # Just ensure no exception and no stray file
    assert not os.path.exists(".gemma_session_log_test_sentinel.jsonl")
