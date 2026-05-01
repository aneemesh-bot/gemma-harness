import subprocess
import shlex
import json
import os

DEFAULT_WHITELIST = ["ls", "cat", "echo", "pwd", "pytest", "git"]
# These operators bypass shell=False restrictions if left in tokens, so we block them entirely.
DANGEROUS_OPERATORS = ["&&", "||", ";", "|", ">", "<", "$"]

def load_whitelist() -> list:
    config_path = "harness_config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
                return data.get("allowed_commands", DEFAULT_WHITELIST)
        except Exception:
            return DEFAULT_WHITELIST
    return DEFAULT_WHITELIST

def execute_command(command: str) -> str:
    whitelist = load_whitelist()
    
    try:
        # Securely parse the command into POSIX tokens
        tokens = shlex.split(command)
        if not tokens:
            return "Error: Empty command."
            
        base_cmd = tokens[0]
        
        # Guardrail 1: Whitelist validation
        if base_cmd not in whitelist:
            return f"Error: Command '{base_cmd}' is blocked. Permitted base commands for this workspace are: {whitelist}."
            
        # Guardrail 2: Operator injection prevention
        for token in tokens:
            if any(op in token for op in DANGEROUS_OPERATORS):
                return "Error: Command contains forbidden shell operators (&&, ||, ;, |, >, <). Command rejected."

        # Guardrail 3: Sandboxed Execution (shell=False) with 15s Timeout
        result = subprocess.run(
            tokens, 
            shell=False, 
            capture_output=True, 
            text=True, 
            timeout=15
        )
        
        # Guardrail 4: Output Truncation for VRAM Protection
        output = result.stdout + result.stderr
        lines = output.splitlines()
        if len(lines) > 50:
            truncated = "\n".join(lines[-50:])
            output = f"[Output too long. Truncated... Showing last 50 lines]\n{truncated}"
            
        status = "Success" if result.returncode == 0 else f"Failed (Exit Code {result.returncode})"
        return f"Command Status: {status}\nOutput:\n{output.strip()}"
        
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 15 seconds. Did you start a server or interactive prompt?"
    except Exception as e:
        return f"Error executing command: {str(e)}"

# --- Verification Block (For isolated testing) ---
if __name__ == "__main__":
    # Test 1: Whitelisted command
    print(execute_command("echo 'Hello World'"))
    
    # Test 2: Blocked command
    print(execute_command("npm install"))
    
    # Test 3: Injection attempt
    print(execute_command("echo 'Test' && rm -rf /"))