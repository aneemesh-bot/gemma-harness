# gemma-harness/main.py

import argparse
from rich.console import Console
from harness.orchestrator import AgentOrchestrator
from harness.session import load_session, clear_session
from harness.ui import TerminalUI

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Gemma-e4b Agent Harness")
    parser.add_argument("--log", metavar="FILE", help="Log all agent events to FILE as JSONL")
    args = parser.parse_args()

    console.print("[bold green]Initializing Gemma-e4b Agent Harness...[/bold green]")
    console.print("[dim]Loading orchestrator and connecting to Ollama...[/dim]")

    try:
        # Initialize the Brain
        # Ensure you have your Ollama server running and the model tag matches your setup
        orchestrator = AgentOrchestrator(model_name="gemma4:e4b")
        ui = TerminalUI(orchestrator, log_file=args.log)

        # Offer to resume a saved session if one exists
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

        # The main interaction loop
        while True:
            try:
                user_input = console.input("\n[bold cyan]You>[/bold cyan] ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['exit', 'quit']:
                    console.print("[dim]Shutting down harness...[/dim]")
                    break

                ui.process_task(user_input)

            except KeyboardInterrupt:
                # Catch Ctrl+C during the input prompt
                console.print("\n[dim]Shutting down harness...[/dim]")
                break

    except Exception as e:
        console.print(f"[bold red]Failed to initialize the agent:[/bold red] {str(e)}")
        console.print("[dim]Ensure Ollama is running and the 'gemma' model is pulled.[/dim]")

if __name__ == "__main__":
    main()