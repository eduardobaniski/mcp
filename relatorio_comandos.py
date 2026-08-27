#!/usr/bin/env python3
"""
relatorio_comandos.py

Lê os logs estruturados gerados pelo comando_logger.py (comandos_AAAA-MM-DD.jsonl)
e exporta em formato de tabela (.txt) ou planilha (.csv), com a saída completa
(stdout/stderr) de cada comando — o que o auditd sozinho não fornece.

Uso:
  ./relatorio_comandos.py                          # mostra hoje, na tela, em txt
  ./relatorio_comandos.py --dias 7                  # últimos 7 dias
  ./relatorio_comandos.py -o relatorio.csv          # exporta para CSV
  ./relatorio_comandos.py -o relatorio.txt          # exporta para TXT
  ./relatorio_comandos.py --log-dir /outro/caminho/logs
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


def carregar_registros(log_dir: Path, dias: int) -> list[dict]:
    registros = []
    hoje = datetime.now(timezone.utc).date()
    for i in range(dias):
        dia = hoje - timedelta(days=i)
        caminho = log_dir / f"comandos_{dia.isoformat()}.jsonl"
        if not caminho.exists():
            continue
        with open(caminho, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue
                try:
                    registros.append(json.loads(linha))
                except json.JSONDecodeError:
                    # linha corrompida/parcial (ex: crash no meio da escrita) — ignora e segue
                    continue
    # mais recente primeiro
    registros.sort(key=lambda r: r.get("timestamp_utc", ""), reverse=True)
    return registros


def truncar(texto: str, limite: int) -> str:
    texto = texto or ""
    texto_uma_linha = texto.replace("\n", " ⏎ ").replace("\r", "")
    if len(texto_uma_linha) > limite:
        return texto_uma_linha[: limite - 1] + "…"
    return texto_uma_linha


def exportar_txt(registros: list[dict], destino) -> None:
    cabecalho = f"{'HORA (UTC)':<26} {'GITHUB':<12} {'RESULT.':<7} {'COD':<5} {'COMANDO':<40} {'SAIDA (stdout/stderr)'}"
    print(cabecalho, file=destino)
    print("-" * len(cabecalho), file=destino)
    for r in registros:
        hora = r.get("timestamp_utc", "")
        usuario_gh = r.get("usuario_github") or "-"
        resultado = "OK" if r.get("ok") else "FALHA"
        cod = r.get("exit_code")
        cod_str = str(cod) if cod is not None else "-"
        comando = truncar(r.get("comando", ""), 40)
        saida = truncar((r.get("stdout") or "") + (r.get("stderr") or ""), 60)
        print(f"{hora:<26} {usuario_gh:<12} {resultado:<7} {cod_str:<5} {comando:<40} {saida}", file=destino)


def exportar_csv(registros: list[dict], destino) -> None:
    campos = [
        "timestamp_utc", "usuario_so", "usuario_github", "diretorio",
        "comando", "ok", "exit_code", "erro", "stdout", "stderr", "duracao_segundos",
    ]
    writer = csv.DictWriter(destino, fieldnames=campos, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    for r in registros:
        writer.writerow({campo: r.get(campo, "") for campo in campos})


def main() -> None:
    parser = argparse.ArgumentParser(description="Relatório dos comandos executados pelo agente MCP (com saída completa).")
    parser.add_argument("--log-dir", default="/home/agente/mcp/logs", help="Diretório onde os .jsonl estão salvos.")
    parser.add_argument("--dias", type=int, default=1, help="Quantos dias (contando hoje) incluir no relatório.")
    parser.add_argument("-o", "--output", help="Arquivo de saída. Extensão .csv gera planilha; qualquer outra gera texto.")
    args = parser.parse_args()

    log_dir = Path(args.log_dir)
    registros = carregar_registros(log_dir, args.dias)

    if not registros:
        print(f"Nenhum registro encontrado em {log_dir} para os últimos {args.dias} dia(s).", file=sys.stderr)
        sys.exit(1)

    formato_csv = bool(args.output) and args.output.lower().endswith(".csv")

    if args.output:
        modo = "w"
        with open(args.output, modo, encoding="utf-8", newline="" if formato_csv else None) as destino:
            if formato_csv:
                exportar_csv(registros, destino)
            else:
                exportar_txt(registros, destino)
        print(f"Relatório salvo em: {args.output} ({'csv' if formato_csv else 'txt'}, {len(registros)} registros)")
    else:
        exportar_txt(registros, sys.stdout)


if __name__ == "__main__":
    main()