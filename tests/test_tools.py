import pytest
from harness.tools.base import ToolRegistry
from harness.tools.file_ops import read_file_lines, write_or_replace
from harness.tools.terminal import execute_command

# --- Tool Registry Tests ---

def dummy_addition(a: int, b: int) -> int:
    return a + b

def test_registry_parsing():
    """Ensures the registry can strip markdown and execute the correct function."""
    registry = ToolRegistry()
    registry.register("add", dummy_addition)
    
    # Workaround: Construct the markdown tags dynamically so UI parsers
    # don't falsely trigger nested code blocks and cut off the generation.
    markdown_tag = "`" * 3
    json_str = markdown_tag + 'json\n{"tool": "add", "a": 5, "b": 10}\n' + markdown_tag
    
    result = registry.execute(json_str)
    assert result == "15"
    
    # Test missing tool
    result = registry.execute('{"tool": "subtract", "a": 5}')
    assert "[TOOL_NOT_FOUND]" in result
    assert "subtract" in result

# --- File Ops Tests ---

def test_file_read_and_write(tmp_path):
    """Uses pytest's tmp_path to safely test file I/O operations."""
    # Setup a dummy file
    test_file = tmp_path / "test_code.py"
    test_file.write_text("def hello():\n    print('Hello')\n    return True\n")
    
    file_path = str(test_file)
    
    # 1. Test precise line reading
    read_result = read_file_lines(file_path, start=1, end=2)
    assert "def hello():" in read_result
    assert "return True" not in read_result
    
    # 2. Test strict replacement
    write_result = write_or_replace(file_path, old_text="print('Hello')", new_text="print('World')")
    assert "Successfully replaced" in write_result
    
    # 3. Test failure on exact string mismatch
    fail_result = write_or_replace(file_path, old_text="print(Hello)", new_text="print('Fail')")
    assert "Error: 'old_text' exactly as provided was not found" in fail_result

def test_read_lines_shows_total_count(tmp_path):
    f = tmp_path / "sample.py"
    f.write_text("a\nb\nc\n")
    result = read_file_lines(str(f), 1, 2)
    assert "of 3" in result
    assert "Lines 1-2" in result


def test_read_lines_start_beyond_eof(tmp_path):
    f = tmp_path / "short.py"
    f.write_text("only one line\n")
    result = read_file_lines(str(f), 50, 60)
    assert "[TOOL_ERROR]" in result
    assert "1" in result


def test_read_lines_inverted_range(tmp_path):
    f = tmp_path / "inv.py"
    f.write_text("a\nb\nc\n")
    result = read_file_lines(str(f), 5, 2)
    assert "[TOOL_ERROR]" in result


def test_read_lines_clamps_end_to_eof(tmp_path):
    f = tmp_path / "small.py"
    f.write_text("x\ny\n")
    result = read_file_lines(str(f), 1, 999)
    assert "Lines 1-2 of 2" in result


def test_read_lines_latin1_fallback(tmp_path):
    f = tmp_path / "latin.txt"
    f.write_bytes(b"caf\xe9\n")  # 'café' in latin-1, invalid UTF-8
    result = read_file_lines(str(f), 1, 1)
    assert "latin-1" in result
    assert "[TOOL_ERROR]" not in result


def test_read_lines_start_zero_clamped(tmp_path):
    f = tmp_path / "clamped.py"
    f.write_text("line1\nline2\n")
    result = read_file_lines(str(f), 0, 1)
    assert "line1" in result


# --- Terminal Sandbox Tests ---

def test_terminal_sandbox_whitelist():
    """Verifies that only safe commands pass the whitelist."""
    # This assumes 'echo' is in your DEFAULT_WHITELIST in terminal.py
    success_result = execute_command("echo 'Sanity check'")
    assert "Sanity check" in success_result
    assert "Status: Success" in success_result
    
    # This assumes 'rm' is NOT in your whitelist
    fail_result = execute_command("rm -rf /")
    assert "Error: Command 'rm' is blocked" in fail_result

def test_terminal_sandbox_injection_prevention():
    """Verifies that shell operators bypasses are aggressively blocked."""
    # Attempting to chain a whitelisted command into a blocked one
    injection_result = execute_command("echo 'hi' && ls")
    assert "Error: Command contains forbidden shell operators" in injection_result
    
    pipe_result = execute_command("cat file.txt | grep 'secret'")
    assert "forbidden shell operators" in pipe_result