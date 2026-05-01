# Gemma-Harness

A lightweight, VRAM-optimized autonomous AI software engineer harness designed to run on (my) laptop via Ollama. 

I have an ASUS with an RTX 3060, with 6 GB VRAM (which can run basic quantized LLMs) and I wanted to experiement with local agentic AI. 
RTX hardware is absolutely amazing for inference, therefore I believe it would be theoretically possible, with enough optimization, to run an agentic loop and design a capable harness to use the model and perform (some) local autonomous software engineering, tool calls, and what have you.

The harness thus employs an intelligent Context Manager that actively compresses, prunes, and summarizes conversation history to prevent Out of Memory (OOM) crashes while maintaining the agent's contextual awareness, akin to industry-standard agentic frameworks.

## Features

* **Autonomous ReAct loop:** Employs a continuous Thought → Action → Observation loop to explore codebases, fix bugs, and run tests.
* **The strict VRAM guardrails (uses the Sliding Window approach):** Automatically monitors token usage. At 80% capacity, it aggressively prunes `<|think|>` reasoning blocks and uses background LLM calls to summarize older conversational history.
* **Sandboxed tool execution:** Prevents accidental codebase destruction or malicious shell commands via a strict `harness_config.json` whitelist.
* **Rich terminal UI:** Provides a beautiful, streaming, multi-colored interface directly in my integrated terminal (works with my VS Code instance).
* **Precise file operations:** Uses exact string replacement (`write_or_replace`) and targeted line reading to manipulate files safely.


## Setup & Installation

1. **Installing dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **HuggingFace Authentication (Optional but I recommend it for optimal tokenization):**
   To ensure 100% accurate token counting for the Context Manager, authenticate your environment with Hugging Face so the `transformers` library can download the Gemma tokenizer.
   ```bash
   pip install -U "huggingface_hub[cli]"
   huggingface-cli login
   ```
3. **Configure Workspace sandbox:**
   A `harness_config.json` file in the root directory must be created before running the agent, defining the permitted terminal commands:
   ```json
   {
     "allowed_commands": ["ls", "cat", "echo", "pwd", "pytest", "git", "python"]
   }
   ```
4. **Start Ollama:**
   Local Ollama server running and the target model is available (I run `gemma4:e4b`).
   ```bash
   ollama serve
   ```

## Usage

Launch the agent from your terminal:
```bash
python main.py
```

You can now interact with the agent autonomously! Type your task (e.g., *"Run pytest, find the failing tests, fix the bug in the source code, and verify it passes"*) and watch it work. To exit, type `exit` or `quit`.
