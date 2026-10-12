#!/bin/bash
# PreToolUse (Edit|Write): bloqueia arquivos que o Claude não deve alterar. Sem jq e sem Python:
# no Windows, `python`/`python3` costumam ser o atalho da Microsoft Store (está no PATH, mas não executa).
INPUT=$(cat)
campo() { printf '%s' "$INPUT" | tr -d '\n' | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p"; }
NOME=$(campo tool_name)
FILE=$(campo file_path | tr '\\' '/' | sed 's#//*#/#g')
if [ -z "$FILE" ]; then
  # Falha fechada: ferramenta de escrita sem caminho legível não passa. Entrada sem escrita (JSON vazio, Bash) passa.
  case "$NOME" in
    Edit|Write|MultiEdit)
      echo "Bloqueado: não consegui ler o file_path de $NOME; por segurança a escrita foi negada." >&2
      exit 2 ;;
  esac
  exit 0
fi
ROOT=$(printf '%s' "$CLAUDE_PROJECT_DIR" | tr '\\' '/' | sed 's#//*#/#g')
REL="${FILE#"$ROOT"/}"
case "$REL" in
  .env|*/.env|*.joblib|backend/*|frontend/*|docs/referencia/*)
    echo "Bloqueado: $REL é protegido neste projeto (CLAUDE.md, regra 9). Peça a alteração a João Paulo." >&2
    exit 2 ;;
esac
exit 0
