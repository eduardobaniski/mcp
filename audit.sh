#!/bin/bash

# Garante que o script seja executado como root ou via sudo
if [ "$EUID" -ne 0 ]; then
  echo -e "\033[1;31mErro: Este script precisa ser executado como root ou usando sudo.\033[0m"
  exit 1
fi

# Executa o ausearch e trata a saída em blocos com o awk
ausearch -k comandos_do_mcp --interpret | awk '
BEGIN { 
    # Imprime o cabeçalho formatado com cores (Ciano para os títulos)
    printf "\033[1;36m%-20s %-12s %-35s %-s\033[0m\n", "HORÁRIO", "USUÁRIO", "DIRETÓRIO", "COMANDO EXECUTA"
    print "------------------------------------------------------------------------------------------------------------------"
}
{
    # Sempre que encontrar a linha de separação do auditd (----), imprime o comando anterior se o bloco estiver completo
    if ($0 ~ /^----/) {
        if (datetime != "" && user != "" && dir != "" && cmd != "") {
            printf "%-20s %-12s %-35s \033[1;32m%-s\033[0m\n", datetime, user, dir, cmd
        }
        # Limpa o buffer para capturar o próximo comando do log
        cmd = ""; datetime = ""; user = ""; dir = ""
    }
}
/^type=SYSCALL/ { 
    # Captura e formata a Data/Hora do evento
    if (match($0, /msg=audit\([^)]+\)/)) {
        datetime = substr($0, RSTART + 10, RLENGTH - 11)
        sub(/:[0-9]+\.[0-9]+/, "", datetime) # Limpa os milissegundos
    }
    # Captura o usuário efetivo que disparou a ação (euid)
    if (match($0, /euid=[^ ]+/)) {
        user = substr($0, RSTART + 5, RLENGTH - 5)
    }
}
/^type=CWD/ {
    # Captura o diretório atual de trabalho (Current Working Directory)
    if (match($0, /cwd="[^"]+"/)) {
        dir = substr($0, RSTART + 5, RLENGTH - 6)
    }
}
/^type=EXECVE/ {
    # Agrupa todos os argumentos sequenciais do comando (a0, a1, a2...) em uma única linha
    for (i=5; i<=NF; i++) {
        if ($i ~ /^a[0-9]+=/) {
            sub(/^a[0-9]+="/, "", $i)
            sub(/"$/, "", $i)
            cmd = cmd $i " "
        }
    }
}
END {
    # Cospe o último comando do arquivo caso o log termine sem a linha separadora "----"
    if (datetime != "" && user != "" && dir != "" && cmd != "") {
        printf "%-20s %-12s %-35s \033[1;32m%-s\033[0m\n", datetime, user, dir, cmd
    }
}'
