#!/bin/bash
#
# relatorio_mcp.sh
# Gera relatório de comandos executados pelo usuário do agente MCP,
# baseado nos logs do auditd (chave: comandos_do_mcp)
#
# Por padrão, mostra os eventos de HOJE, com os mais recentes primeiro.
#
# Uso:
#   ./relatorio_mcp.sh
#   ./relatorio_mcp.sh --start yesterday
#   ./relatorio_mcp.sh --start "07/01/2026 00:00:00" --end "07/10/2026 23:59:59"
#   ./relatorio_mcp.sh -o arquivo.txt

set -euo pipefail

CHAVE="comandos_do_mcp"
OUTFILE=""
AUSEARCH_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)
      OUTFILE="$2"
      shift 2
      ;;
    *)
      AUSEARCH_ARGS+=("$1")
      shift
      ;;
  esac
done

# Se nenhum --start/--end foi passado, assume "hoje" como padrão,
# assim o relatório sempre mostra o mais recente sem precisar digitar nada.
if [[ ${#AUSEARCH_ARGS[@]} -eq 0 ]]; then
  AUSEARCH_ARGS=(--start today)
fi

if [[ $EUID -ne 0 ]]; then
  echo "Este script precisa rodar com sudo (o ausearch exige root para ler os logs de auditoria)." >&2
  exit 1
fi

gerar_linhas() {
  ausearch -k "$CHAVE" -i "${AUSEARCH_ARGS[@]}" 2>/dev/null | awk '
    /^type=PROCTITLE/ {
      cmd = $0
      sub(/.*proctitle=/, "", cmd)
    }
    /^type=CWD/ {
      dir = $0
      sub(/.*cwd=/, "", dir)
      sub(/ *$/, "", dir)
    }
    /^type=SYSCALL/ {
      ts_full = $0
      match(ts_full, /audit\([^)]+\)/)
      ts = substr(ts_full, RSTART+6, RLENGTH-7)
      sub(/:[0-9]+$/, "", ts)
      user = ""
      n = split($0, campos, " ")
      for (i = 1; i <= n; i++) {
        if (campos[i] ~ /^uid=/) {
          user = campos[i]
          sub(/^uid=/, "", user)
        }
      }
      printf "%-22s %-10s %-25s %s\n", ts, user, dir, cmd
      cmd = ""
      dir = ""
    }
  '
}

gerar_relatorio() {
  printf "%-22s %-10s %-25s %s\n" "HORA" "USUARIO" "DIRETORIO" "COMANDO"
  printf "%-22s %-10s %-25s %s\n" "----" "-------" "---------" "-------"
  # tac inverte a ordem: mais recente aparece primeiro, no topo
  gerar_linhas | tac
}

if [[ -n "$OUTFILE" ]]; then
  gerar_relatorio | tee "$OUTFILE"
  echo ""
  echo "Relatório também salvo em: $OUTFILE"
else
  gerar_relatorio
fi
