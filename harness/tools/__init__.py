from .base import ToolRegistry
from .file_ops import list_directory, search_codebase, read_file_lines, write_or_replace
from .terminal import execute_command

def get_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register("list_directory", list_directory)
    registry.register("search_codebase", search_codebase)
    registry.register("read_file_lines", read_file_lines)
    registry.register("write_or_replace", write_or_replace)
    registry.register("execute_command", execute_command)
    
    # The ending condition. The orchestrator will listen for this exact prefix to halt the loop.
    registry.register("task_complete", lambda message: f"TASK_COMPLETE: {message}")
    
    return registry