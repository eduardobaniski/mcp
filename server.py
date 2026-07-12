from __future__ import annotations

import os
import subprocess
from typing import Any

from fastmcp import FastMCP
import uvicorn

# Name shown to MCP clients
mcp = FastMCP("terminal-command-server")


@mcp.tool()
def execute_command(command: str, timeout_seconds: int = 30) -> dict[str, Any]:
    """Execute a shell command on the host machine and return its output.

    Args:
        command: Full command line to execute.
        timeout_seconds: Maximum time allowed before the process is terminated.
    """
    if not command or not command.strip():
        return {
            "ok": False,
            "error": "Command cannot be empty.",
            "exit_code": None,
            "stdout": "",
            "stderr": "",
        }

    timeout_seconds = max(1, min(timeout_seconds, 300))

    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=os.getcwd(),
        )
        return {
            "ok": completed.returncode == 0,
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "error": f"Command timed out after {timeout_seconds} seconds.",
            "exit_code": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
        }
    except Exception as exc:  # Defensive catch so tool always returns structured output
        return {
            "ok": False,
            "error": str(exc),
            "exit_code": None,
            "stdout": "",
            "stderr": "",
        }


    

mcp.run(transport="http", host="0.0.0.0", port=8000)