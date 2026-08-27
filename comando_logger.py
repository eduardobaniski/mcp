"""
comando_logger.py

Log estruturado do servidor MCP. Complementa o auditd: o auditd registra
a INVOCAÇÃO do comando (usuário do SO, quando, o quê), mas não a saída
(stdout/stderr) nem QUEM de fato disparou (a identidade GitHub por trás
da sessão OAuth) — só o processo do servidor tem essa informação, então
o log precisa ser gerado aqui dentro, não reconstruído do auditd depois.

Grava um objeto JSON por linha (JSON Lines), um arquivo por dia, em
MCP_LOG_DIR (default: /home/agente/mcp/logs).
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

LOG_DIR = Path(os.environ.get("MCP_LOG_DIR", "/home/agente/mcp/logs"))


def _caminho_log_do_dia() -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    nome = datetime.now(timezone.utc).strftime("comandos_%Y-%m-%d.jsonl")
    return LOG_DIR / nome


def registrar_execucao(
    comando: str,
    usuario_so: str,
    usuario_github: Optional[str],
    diretorio: str,
    ok: bool,
    exit_code: Optional[int],
    stdout: str,
    stderr: str,
    duracao_segundos: float,
    erro: Optional[str] = None,
) -> None:
    """Grava uma linha JSON com todos os dados da execução."""
    registro = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "usuario_so": usuario_so,
        "usuario_github": usuario_github,
        "diretorio": diretorio,
        "comando": comando,
        "ok": ok,
        "exit_code": exit_code,
        "erro": erro,
        "stdout": stdout,
        "stderr": stderr,
        "duracao_segundos": round(duracao_segundos, 3),
    }
    caminho = _caminho_log_do_dia()
    with open(caminho, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")