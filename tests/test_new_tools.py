"""
Tests for the 6 new tools added in the second tool-expansion pass:
grep_lines, append_to_file, delete_file, move_file, check_syntax, tree_directory.
"""
import os
import pytest
from harness.tools.file_ops import (
    grep_lines, append_to_file, delete_file,
    move_file, check_syntax, tree_directory,
)
from harness.tools import get_tool_registry


# ---------------------------------------------------------------------------
# grep_lines
# ---------------------------------------------------------------------------

def test_grep_lines_finds_match(tmp_path):
    f = tmp_path / "hello.py"
    f.write_text("def greet():\n    print('Hello World')\n    return True\n")
    result = grep_lines("Hello World", path=str(tmp_path))
    assert "hello.py" in result
    assert "Hello World" in result
    # Must include line number
    assert ":2:" in result


def test_grep_lines_no_match(tmp_path):
    f = tmp_path / "code.py"
    f.write_text("x = 1\n")
    result = grep_lines("nonexistent_keyword_xyz", path=str(tmp_path))
    assert "No matches" in result


def test_grep_lines_respects_max_results(tmp_path):
    # Create a file with 40 matching lines
    f = tmp_path / "many.py"
    f.write_text("\n".join(f"# match {i}" for i in range(40)) + "\n")
    result = grep_lines("match", path=str(tmp_path), max_results=10)
    assert "TRUNCATED" in result
    # Should show exactly 10 results before the truncation notice
    lines = result.strip().splitlines()
    match_lines = [l for l in lines if "many.py:" in l]
    assert len(match_lines) == 10


# ---------------------------------------------------------------------------
# append_to_file
# ---------------------------------------------------------------------------

def test_append_to_file_adds_content(tmp_path):
    f = tmp_path / "log.txt"
    f.write_text("line one\n")
    result = append_to_file(str(f), "line two\n")
    assert "Successfully appended" in result
    assert f.read_text() == "line one\nline two\n"


def test_append_to_file_rejects_missing_file(tmp_path):
    result = append_to_file(str(tmp_path / "ghost.txt"), "data")
    assert "Error" in result
    assert "does not exist" in result


# ---------------------------------------------------------------------------
# delete_file
# ---------------------------------------------------------------------------

def test_delete_file_removes_file(tmp_path):
    f = tmp_path / "trash.py"
    f.write_text("# delete me")
    result = delete_file(str(f))
    assert "Successfully deleted" in result
    assert not f.exists()


def test_delete_file_rejects_directory(tmp_path):
    result = delete_file(str(tmp_path))
    assert "Error" in result
    assert "directory" in result


def test_delete_file_rejects_missing(tmp_path):
    result = delete_file(str(tmp_path / "no_such_file.txt"))
    assert "Error" in result
    assert "not found" in result


# ---------------------------------------------------------------------------
# move_file
# ---------------------------------------------------------------------------

def test_move_file_renames(tmp_path):
    src = tmp_path / "old_name.py"
    src.write_text("content")
    dst = tmp_path / "new_name.py"
    result = move_file(str(src), str(dst))
    assert "Successfully moved" in result
    assert not src.exists()
    assert dst.read_text() == "content"


def test_move_file_rejects_missing_src(tmp_path):
    result = move_file(str(tmp_path / "ghost.py"), str(tmp_path / "dest.py"))
    assert "Error" in result
    assert "does not exist" in result


def test_move_file_rejects_existing_dst(tmp_path):
    src = tmp_path / "src.py"
    src.write_text("a")
    dst = tmp_path / "dst.py"
    dst.write_text("b")
    result = move_file(str(src), str(dst))
    assert "Error" in result
    assert "already exists" in result
    # src must still be intact
    assert src.exists()


# ---------------------------------------------------------------------------
# check_syntax
# ---------------------------------------------------------------------------

def test_check_syntax_valid_file(tmp_path):
    f = tmp_path / "valid.py"
    f.write_text("def add(a, b):\n    return a + b\n")
    result = check_syntax(str(f))
    assert "Syntax OK" in result


def test_check_syntax_broken_file(tmp_path):
    f = tmp_path / "broken.py"
    f.write_text("def foo(\n    pass\n")  # unclosed parenthesis
    result = check_syntax(str(f))
    assert "Syntax error" in result or "SyntaxError" in result


# ---------------------------------------------------------------------------
# tree_directory
# ---------------------------------------------------------------------------

def test_tree_directory_basic(tmp_path):
    (tmp_path / "a.py").write_text("")
    sub = tmp_path / "subdir"
    sub.mkdir()
    (sub / "b.py").write_text("")
    result = tree_directory(str(tmp_path), max_depth=2)
    assert "a.py" in result
    assert "subdir" in result
    assert "b.py" in result


def test_tree_directory_respects_max_depth(tmp_path):
    deep = tmp_path / "level1" / "level2" / "level3"
    deep.mkdir(parents=True)
    (deep / "deep_file.py").write_text("")
    result = tree_directory(str(tmp_path), max_depth=2)
    # level1 and level2 should appear, but not level3's contents
    assert "level1" in result
    assert "level2" in result
    assert "deep_file.py" not in result


def test_tree_directory_skips_venv(tmp_path):
    venv = tmp_path / "venv"
    venv.mkdir()
    (venv / "something.py").write_text("")
    (tmp_path / "real.py").write_text("")
    result = tree_directory(str(tmp_path), max_depth=3)
    assert "real.py" in result
    assert "something.py" not in result


# ---------------------------------------------------------------------------
# Registry integration
# ---------------------------------------------------------------------------

def test_all_new_tools_registered():
    registry = get_tool_registry()
    for name in ("grep_lines", "append_to_file", "delete_file",
                 "move_file", "check_syntax", "tree_directory"):
        assert name in registry.tools, f"Tool '{name}' not registered"
