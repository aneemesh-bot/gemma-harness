import argparse
import json
import os
import readline  # noqa: F401 — enables arrow-key navigation and history in input()

from rich.console import Console

from .orchestrator import AgentOrchestrator
from .session import load_session, clear_session
from .ui import TerminalUI

console = Console()

_DEFAULT_CONFIG = {
    "allowed_commands": ["ls", "cat", "echo", "pwd", "pytest", "git", "python"]
}

_CONFIG_FILE = "harness_config.json"


def _cmd_init() -> None:
    if os.path.exists(_CONFIG_FILE):
        console.print(f"[yellow]{_CONFIG_FILE} already exists — skipping.[/yellow]")
        return
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(_DEFAULT_CONFIG, f, indent=2)
        f.write("\n")
    console.print(f"[bold green]Created {_CONFIG_FILE}[/bold green] with default command whitelist.")


def _cmd_run(args: argparse.Namespace) -> None:
    console.print("[bold green]Initializing Gemma Agent Harness...[/bold green]")
    console.print("[dim]Loading orchestrator and connecting to Ollama...[/dim]")

    try:
        orchestrator = AgentOrchestrator(model_name=args.model, base_url=args.ollama_url)
        ui = TerminalUI(orchestrator, log_file=args.log)

        saved = load_session()
        if saved:
            console.print("[yellow]A previous session checkpoint was found.[/yellow]")
            choice = console.input("[bold yellow]Resume it? (y/n): [/bold yellow]").strip().lower()
            if choice == "y":
                orchestrator.context_manager.messages = saved
                console.print("[dim]Session resumed.[/dim]")
            else:
                clear_session()
                console.print("[dim]Starting fresh session.[/dim]")

        console.print("[bold green]Agent Ready.[/bold green] Type 'exit' or 'quit' to terminate.")
        console.print("---")

        while True:
            try:
                user_input = console.input("\n[bold cyan]You>[/bold cyan] ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["exit", "quit"]:
                    console.print("[dim]Shutting down harness...[/dim]")
                    break

                ui.process_task(user_input)

            except KeyboardInterrupt:
                console.print("\n[dim]Shutting down harness...[/dim]")
                break

    except Exception as e:
        console.print(f"[bold red]Failed to initialize the agent:[/bold red] {str(e)}")
        console.print("[dim]Ensure Ollama is running and the model is pulled.[/dim]")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="gemma-harness",
        description="Lightweight autonomous AI agent harness for local Ollama models",
    )
    subparsers = parser.add_subparsers(dest="command")

    # gemma-harness init
    subparsers.add_parser("init", help=f"Create a starter {_CONFIG_FILE} in the current directory")

    # gemma-harness run  (also the default when no subcommand is given)
    run_parser = subparsers.add_parser("run", help="Start the interactive agent (default)")
    run_parser.add_argument("--log", metavar="FILE", help="Log all agent events to FILE as JSONL")
    run_parser.add_argument("--model", default="gemma4:e4b", metavar="TAG",
                            help="Ollama model tag to use (default: gemma4:e4b)")
    run_parser.add_argument("--ollama-url", default="http://127.0.0.1:11434", metavar="URL",
                            dest="ollama_url", help="Ollama base URL (default: http://127.0.0.1:11434)")

    args = parser.parse_args()

    if args.command == "init":
        _cmd_init()
    else:
        # Plain `gemma-harness` or `gemma-harness run` — both land here
        if args.command is None:
            # Re-parse treating all args as run-parser args
            args = run_parser.parse_args()
        _cmd_run(args)
