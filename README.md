# Python MCP Terminal Command Server

This project provides an MCP server that exposes one tool:

- `execute_command(command, timeout_seconds=30)`

The tool runs a command on the host machine and returns:

- `ok` (boolean)
- `exit_code` (int or null)
- `stdout` (string)
- `stderr` (string)
- `error` (string, only when applicable)

## 1) Create and activate a virtual environment (Windows PowerShell)

```powershell
uv venv
\.venv\Scripts\Activate.ps1
```

## 2) Install dependencies

```powershell
uv sync
```

## 3) Run the MCP server

```powershell
uv run python server.py
```

The server runs over stdio, which is what most MCP clients expect for local servers.

## 4) Example MCP client config

Use your MCP client configuration mechanism and point it to this server process.
A typical local stdio config looks like this:

```json
{
  "mcpServers": {
    "terminal": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "c:/Users/cadub/mcp_command",
        "python",
        "server.py"
      ]
    }
  }
}
```

This avoids the startup issue where the client launches from `C:/Windows/System32` and cannot find `server.py`.

## Troubleshooting

- Ensure `uv` is installed and on PATH.
- If your MCP client still fails to launch, check stderr logs from the server. The server now logs startup cwd to stderr.

## Security note

This server executes arbitrary shell commands. Only run it in trusted environments.
