import json
import os
from typing import List, Dict, Optional

SESSION_FILE = ".gemma_session.json"


def save_session(messages: List[Dict[str, str]]) -> None:
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2)


def load_session() -> Optional[List[Dict[str, str]]]:
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def clear_session() -> None:
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
