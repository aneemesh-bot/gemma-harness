# Gemma-Harness

A lightweight, VRAM-optimized autonomous AI software engineer harness designed to run locally via Ollama. 

Built specifically for environments with strict VRAM limits (e.g., 6 GB), this harness employs an intelligent Context Manager that actively compresses, prunes, and summarizes conversation history to prevent Out of Memory (OOM) crashes while maintaining the agent's contextual awareness.

## Features

* **Autonomous ReAct Loop:** Employs a continuous Thought → Action → Observation loop to explore codebases, fix bugs, and run tests.
* **VRAM Guardrails (Sliding Window):** Automatically monitors token usage. At 80% capacity, it aggressively prunes `<|think|>` reasoning blocks and uses background LLM calls to summarize older conversational history.
* **Sandboxed Tool Execution:** Prevents accidental codebase destruction or malicious shell commands via a strict `harness_config.json` whitelist.
* **Rich Terminal UI:** Provides a beautiful, streaming, multi-colored interface directly in your integrated terminal (e.g., VS Code).
* **Precise File Operations:** Uses exact string replacement (`write_or_replace`) and targeted line reading to manipulate files safely.

## Project Structure

```text
gemma-harness/
│
├── harness/                    # Core application package
│   ├── __init__.py
│   ├── orchestrator.py         # The ReAct loop and state machine
│   ├── llm_client.py           # Handles HTTP requests to the Ollama API
│   ├── context_manager.py      # Token counting, sliding window, and summarization
│   ├── prompt.py               # Immutable system instructions & persona
│   ├── tools/                  # The tool registry
│   │   ├── __init__.py
│   │   ├── base.py             # Tool schemas and routing logic
│   │   ├── file_ops.py         # read_lines, write_replace, list_dir
│   │   └── terminal.py         # execute_command with strict whitelisting
│   └── ui.py                   # The Rich terminal interface
│
├── harness_config.json         # Workspace-specific config (tool whitelists) (User generated)
├── main.py                     # Entry point to launch the CLI
└── requirements.txt            # Project dependencies
```

## Setup & Installation

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Hugging Face Authentication (Optional but Recommended):**
   To ensure 100% accurate token counting for the Context Manager, authenticate your environment with Hugging Face so the `transformers` library can download the Gemma tokenizer.
   ```bash
   pip install -U "huggingface_hub[cli]"
   huggingface-cli login
   ```
3. **Configure Your Workspace Sandbox:**
   Create a `harness_config.json` file in the root directory where you plan to run the agent, defining the permitted terminal commands:
   ```json
   {
     "allowed_commands": ["ls", "cat", "echo", "pwd", "pytest", "git", "python"]
   }
   ```
4. **Start Ollama:**
   Ensure your local Ollama server is running and the target model is available (e.g., `gemma4:e4b`).
   ```bash
   ollama serve
   ```

## Usage

Launch the agent from your terminal:
```bash
python main.py
```

You can now interact with the agent autonomously! Type your task (e.g., *"Run pytest, find the failing tests, fix the bug in the source code, and verify it passes"*) and watch it work. To exit, type `exit` or `quit`.
