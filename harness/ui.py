import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.theme import Theme
from rich.live import Live
from rich.spinner import Spinner

# Create a custom theme for different agent states
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red",
    "success": "bold green",
})

console = Console(theme=custom_theme)

class TerminalUI:
    """
    Handles the rendering of the agent's state, streaming output, and tool results.
    """
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def process_task(self, prompt: str):
        """Runs the orchestrator and manages the live terminal updates."""
        console.print(Panel(f"[bold white]{prompt}[/bold white]", title="User Input", border_style="blue"))
        
        # We use a simple state machine to manage the streaming output
        current_status = "Initializing..."
        
        try:
            for event_type, data in self.orchestrator.run_task(prompt):
                if event_type == "status":
                    # Print status updates in a muted color
                    console.print(f"\n[info]⚙ {data}[/info]")
                    
                elif event_type == "stream":
                    # Print the raw stream directly to standard out for real-time feel
                    sys.stdout.write(data)
                    sys.stdout.flush()
                    
                elif event_type == "observation":
                    # Wrap tool observations in a distinct panel so they don't blend with thoughts
                    # Truncate visually if it's massive, though the terminal tool already handles most of this
                    console.print("\n")
                    console.print(Panel(data, title="Tool Observation", border_style="yellow"))
                    
                elif event_type == "complete":
                    console.print("\n")
                    console.print(Panel(Markdown(data), title="Task Complete", border_style="success"))
                    
                elif event_type == "error":
                    console.print("\n")
                    console.print(Panel(data, title="System Error", border_style="danger"))
                    
        except KeyboardInterrupt:
            console.print("\n[danger]Task interrupted by user. Halting orchestrator.[/danger]")