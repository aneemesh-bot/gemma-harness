# Gemma-Harness

A lightweight, VRAM-optimized autonomous AI software engineer harness designed to run on (my) laptop via Ollama. 

I have an ASUS with an RTX 3060, with 6 GB VRAM (which can run basic quantized LLMs) and I wanted to experiment with local agentic AI. 
RTX hardware is absolutely amazing for inference, therefore I believe it would be theoretically possible, with enough optimization, to run an agentic loop and design a capable harness to use the model and perform (some) local autonomous software engineering, tool calls, and what have you.

The harness employs an intelligent Context Manager that actively compresses, prunes, and summarizes conversation history to prevent Out of Memory (OOM) crashes while maintaining the agent's contextual awareness, akin to industry-standard agentic frameworks.

## Features

* **Autonomous ReAct loop:** Employs a continuous Thought → Action → Observation loop to explore codebases, fix bugs, and run tests.
* **Strict VRAM guardrails (Sliding Window):** Automatically monitors token usage. At 80% capacity, it aggressively prunes `<|think|>` reasoning blocks and uses background LLM calls to summarize older conversational history. Context window size is read dynamically from the running Ollama model, so the threshold is always calibrated correctly.
* **Resilient LLM client:** Retries transient Ollama connection errors up to 3 times with exponential backoff (1s → 2s → 4s) before surfacing an error, so a momentary hiccup doesn't kill a long task.
* **Sandboxed tool execution:** Prevents accidental codebase destruction or malicious shell commands via a strict `harness_config.json` whitelist, operator injection detection, and a 15-second timeout.
* **Structured tool errors:** The tool registry returns typed error prefixes (`[PARSE_ERROR]`, `[TOOL_NOT_FOUND]`, `[EXECUTION_ERROR]`) so the model can self-correct more precisely.
* **Session persistence:** Conversation history is checkpointed to `.gemma_session.json` after every step. On restart the harness offers to resume or start fresh, so long-running tasks survive process restarts.
* **Session logging:** Pass `--log <file>` to record every agent event (inputs, streams, observations, completions) as newline-delimited JSON for post-hoc analysis or debugging.
* **Rich terminal UI:** Provides a beautiful, streaming, multi-colored interface directly in my integrated terminal (works with my VS Code instance).

## Tool Inventory

The agent has access to 13 tools:

| Tool | Description |
|------|-------------|
| `tree_directory` | Recursive directory tree up to a configurable depth. Best first call for project exploration. |
| `list_directory` | Flat listing of a single directory. |
| `grep_lines` | Search for a keyword and return matching lines **with file:line numbers**. More precise than `search_codebase`. |
| `search_codebase` | Return filenames that contain a keyword (no line numbers). |
| `read_file_lines` | Read a specific line range from a file (1-indexed). |
| `create_file` | Create a new file. Fails if the file already exists. |
| `append_to_file` | Append content to an existing file without needing to know its exact contents. |
| `write_or_replace` | Exact-string find-and-replace within a file. Must match existing text precisely. |
| `check_syntax` | Run `python -m py_compile` on a file. Catches typos before an expensive `pytest` run. |
| `delete_file` | Delete a single file. Refuses to delete directories. |
| `move_file` | Rename or move a file. Fails if the destination already exists. |
| `execute_command` | Run a whitelisted terminal command in a sandboxed subprocess. |
| `task_complete` | Signal task completion and halt the loop. |

## Setup & Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **HuggingFace Authentication (optional but recommended for accurate tokenization):**
   ```bash
   pip install -U "huggingface_hub[cli]"
   huggingface-cli login
   ```
   Without this, the Context Manager falls back to a ~4 chars/token approximation.

3. **Configure the workspace sandbox:**
   Create `harness_config.json` in the project root to define permitted terminal commands:
   ```json
   {
     "allowed_commands": ["ls", "cat", "echo", "pwd", "pytest", "git", "python"]
   }
   ```

4. **Start Ollama:**
   ```bash
   ollama serve
   ```
   The harness auto-detects the model's context window size via the Ollama API, so any model tag works — just update `model_name` in `main.py`.

## Usage

Launch the agent:
```bash
python main.py
```

To persist a full event log for debugging or replay:
```bash
python main.py --log session.jsonl
```

On startup, if a previous session checkpoint exists (`.gemma_session.json`), the harness will ask whether to resume it or start fresh.

Type your task (e.g., *"Run pytest, find the failing tests, fix the bug in the source code, and verify it passes"*) and watch it work. Type `exit` or `quit` to terminate.

## Running Tests

```bash
pytest tests/ -v
```

The test suite covers the context manager, all 13 tools, retry/backoff logic, session persistence, and session logging.
