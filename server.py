from __future__ import annotations

import os
import subprocess
import time
from typing import Any, Optional
from dotenv import load_dotenv

from fastmcp import FastMCP
import uvicorn

from fastmcp.server.auth.providers.github import GitHubProvider
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_access_token

from comando_logger import registrar_execucao

load_dotenv()

auth = GitHubProvider(
    client_id=os.environ["GITHUB_CLIENT_ID"],
    client_secret=os.environ["GITHUB_CLIENT_SECRET"],
    base_url=os.environ.get("BASE_URL", "http://localhost:8000"),
    allowed_client_redirect_uris=[
        "https://claude.ai/api/mcp/auth_callback",  # necessário pro Claude web
    ],
)
ALLOWED_USERS = {"user"}  # troque pelo seu username do GitHub

class AllowlistMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        token = get_access_token()
        username = token.claims.get("login")
        if username not in ALLOWED_USERS:
            raise ToolError("Acesso negado: usuário não autorizado.")
        return await call_next(context)


# Name shown to MCP clients
mcp = FastMCP("terminal-command-server-authteste", auth=auth)
mcp.add_middleware(AllowlistMiddleware())


def _usuario_github_atual() -> Optional[str]:
    """Extrai o login do GitHub do token OAuth da sessão atual, se houver.

    Isolado em função própria e protegido por try/except porque o logging
    não deve, em hipótese alguma, quebrar a execução do comando em si —
    se por algum motivo não houver token disponível no contexto, registramos
    None em vez de propagar erro.
    """
    try:
        token = get_access_token()
        return token.claims.get("login")
    except Exception:
        return None


@mcp.tool()
def execute_command(command: str, timeout_seconds: int = 30) -> dict[str, Any]:
    """Execute a shell command on the host machine and return its output.

    Args:
        command: Full command line to execute.
        timeout_seconds: Maximum time allowed before the process is terminated.
    """
    usuario_so = os.environ.get("USER") or os.environ.get("LOGNAME") or "desconhecido"
    usuario_github = _usuario_github_atual()
    diretorio = os.getcwd()

    if not command or not command.strip():
        registrar_execucao(
            comando=command,
            usuario_so=usuario_so,
            usuario_github=usuario_github,
            diretorio=diretorio,
            ok=False,
            exit_code=None,
            stdout="",
            stderr="",
            duracao_segundos=0.0,
            erro="Command cannot be empty.",
        )
        return {
            "ok": False,
            "error": "Command cannot be empty.",
            "exit_code": None,
            "stdout": "",
            "stderr": "",
        }

    timeout_seconds = max(1, min(timeout_seconds, 300))
    inicio = time.monotonic()

    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=os.getcwd(),
        )
        duracao = time.monotonic() - inicio
        resultado = {
            "ok": completed.returncode == 0,
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
        registrar_execucao(
            comando=command,
            usuario_so=usuario_so,
            usuario_github=usuario_github,
            diretorio=diretorio,
            ok=resultado["ok"],
            exit_code=resultado["exit_code"],
            stdout=resultado["stdout"],
            stderr=resultado["stderr"],
            duracao_segundos=duracao,
        )
        return resultado

    except subprocess.TimeoutExpired as exc:
        duracao = time.monotonic() - inicio
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        erro = f"Command timed out after {timeout_seconds} seconds."
        registrar_execucao(
            comando=command,
            usuario_so=usuario_so,
            usuario_github=usuario_github,
            diretorio=diretorio,
            ok=False,
            exit_code=None,
            stdout=stdout,
            stderr=stderr,
            duracao_segundos=duracao,
            erro=erro,
        )
        return {
            "ok": False,
            "error": erro,
            "exit_code": None,
            "stdout": stdout,
            "stderr": stderr,
        }

    except Exception as exc:  # Defensive catch so tool always returns structured output
        duracao = time.monotonic() - inicio
        registrar_execucao(
            comando=command,
            usuario_so=usuario_so,
            usuario_github=usuario_github,
            diretorio=diretorio,
            ok=False,
            exit_code=None,
            stdout="",
            stderr="",
            duracao_segundos=duracao,
            erro=str(exc),
        )
        return {
            "ok": False,
            "error": str(exc),
            "exit_code": None,
            "stdout": "",
            "stderr": "",
        }


mcp.run(transport="http", host="0.0.0.0", port=8000)