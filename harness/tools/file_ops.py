import os

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