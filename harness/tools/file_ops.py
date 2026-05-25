import os
import shutil
import subprocess

def list_directory(path: str = ".") -> str:
    try:
        items = os.listdir(path)
        return f"Directory contents of '{path}':\n" + "\n".join(items)
    except Exception as e:
        return f"Error reading directory: {str(e)}"

def search_codebase(keyword: str, path: str = ".") -> str:
    results = []
    try:
        for root, _, files in os.walk(path):
            # Skip hidden/binary directories to save time and VRAM
            if any(x in root for x in ['.git', 'node_modules', '__pycache__', 'venv']):
                continue
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        if keyword in f.read():
                            results.append(filepath)
                except (UnicodeDecodeError, FileNotFoundError):
                    pass
                    
        if not results:
            return f"Keyword '{keyword}' not found."
        return f"Keyword '{keyword}' found in:\n" + "\n".join(results)
    except Exception as e:
        return f"Error searching codebase: {str(e)}"

def read_file_lines(path: str, start: int, end: int) -> str:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # Ensure 1-indexed logic for the model
        snippet = lines[start-1:end]
        return f"--- {path} (Lines {start}-{end}) ---\n" + "".join(snippet)
    except Exception as e:
        return f"Error reading file lines: {str(e)}"

def create_file(path: str, content: str) -> str:
    try:
        if os.path.exists(path):
            return f"Error: File '{path}' already exists. Use write_or_replace to modify it."
        os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully created {path}."
    except Exception as e:
        return f"Error creating file: {str(e)}"

def write_or_replace(path: str, old_text: str, new_text: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        if old_text not in content:
            return "Error: 'old_text' exactly as provided was not found in the file. Use read_file_lines to verify the exact string."

        updated_content = content.replace(old_text, new_text, 1)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        return f"Successfully replaced text in {path}."
    except Exception as e:
        return f"Error modifying file: {str(e)}"

_SKIP_DIRS = {'.git', 'node_modules', '__pycache__', 'venv', '.venv'}

def grep_lines(keyword: str, path: str = ".", max_results: int = 30) -> str:
    """Search files for keyword and return matching lines with line numbers."""
    results = []
    try:
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for lineno, line in enumerate(f, 1):
                            if keyword in line:
                                results.append(f"{filepath}:{lineno}: {line.rstrip()}")
                                if len(results) >= max_results:
                                    return (
                                        "\n".join(results)
                                        + f"\n[TRUNCATED — more than {max_results} matches. Narrow your keyword.]"
                                    )
                except (UnicodeDecodeError, FileNotFoundError):
                    pass
    except Exception as e:
        return f"Error searching: {str(e)}"

    if not results:
        return f"No matches for '{keyword}'."
    return f"{len(results)} match(es) for '{keyword}':\n" + "\n".join(results)


def append_to_file(path: str, content: str) -> str:
    """Append content to an existing file."""
    try:
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist. Use create_file to create it first."
        with open(path, 'a', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully appended to {path}."
    except Exception as e:
        return f"Error appending to file: {str(e)}"


def delete_file(path: str) -> str:
    """Delete a single file. Refuses to delete directories."""
    try:
        if os.path.isdir(path):
            return f"Error: '{path}' is a directory. This tool only deletes files."
        os.remove(path)
        return f"Successfully deleted {path}."
    except FileNotFoundError:
        return f"Error: File '{path}' not found."
    except Exception as e:
        return f"Error deleting file: {str(e)}"


def move_file(src: str, dst: str) -> str:
    """Move or rename a file. Fails if destination already exists."""
    try:
        if not os.path.exists(src):
            return f"Error: Source '{src}' does not exist."
        if os.path.exists(dst):
            return f"Error: Destination '{dst}' already exists. Remove it first."
        shutil.move(src, dst)
        return f"Successfully moved '{src}' to '{dst}'."
    except Exception as e:
        return f"Error moving file: {str(e)}"


def check_syntax(path: str) -> str:
    """Check Python syntax for a file without executing it."""
    try:
        result = subprocess.run(
            ["python", "-m", "py_compile", path],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return f"Syntax OK: {path}"
        return f"Syntax error in {path}:\n{result.stderr.strip()}"
    except Exception as e:
        return f"Error checking syntax: {str(e)}"


def tree_directory(path: str = ".", max_depth: int = 3) -> str:
    """Recursive directory listing formatted as a tree, up to max_depth levels."""
    lines = [f"{path}/"]

    def _walk(current_path: str, prefix: str, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            entries = sorted(os.listdir(current_path))
        except PermissionError:
            return
        entries = [e for e in entries if e not in _SKIP_DIRS]
        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            full_path = os.path.join(current_path, entry)
            lines.append(f"{prefix}{connector}{entry}")
            if os.path.isdir(full_path):
                extension = "    " if is_last else "│   "
                _walk(full_path, prefix + extension, depth + 1)

    _walk(path, "", 1)
    return "\n".join(lines)