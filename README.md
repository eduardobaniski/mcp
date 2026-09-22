# Servidor MCP para Avaliação da Segurança e Fortalecimento de Sistemas Linux

Este repositório contém os arquivos e logs utilizados no desenvolvimento do meu trabalho de conclusão de curso. O objetivo do servidor é utilizar o protocolo MCP para avaliar a capacidade de um LLM analisar a segurança de um servidor Linux

O servidor contém apenas uma ferramenta:

- `execute_command(command, timeout_seconds=30)`

A ferramenta recebe um comando e retorna os seguintes dados:

- `ok` (boolean)
- `exit_code` (int or null)
- `stdout` (string)
- `stderr` (string)
- `error` (string, quando for o caso)

## 1) Criar um ambiente

```powershell
uv venv
\.venv\Scripts\Activate.ps1
```

## 2) Instalar as dependências

```powershell
uv sync
```

## 3) Rodar o servidor

```powershell
uv run python server.py
```

O servidor está configurado para transporte via HTTP. Portanto, é necessário expor uma porta redirecionando para a porta do servidor MCP (porta 8000)


## Aviso de segurança

Este servidor é equivalente a um shell remoto. Utilize apenas em servidores sem dados sensíveis. Utilize por sua conta e risco