#!/bin/bash
# PreToolUse (Edit|Write): bloqueia arquivos que o Claude não deve alterar. Sem jq: usa Python.
PY=$(command -v python3 || command -v python || command -v py)
[ -z "$PY" ] && { echo "protect-files: Python não encontrado; hook desativado." >&2; exit 0; }
INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | "$PY" -c 'import sys,json
try: print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))
except Exception: print("")')
[ -z "$FILE" ] && exit 0
FILE="${FILE//\\//}"
ROOT="${CLAUDE_PROJECT_DIR//\\//}"
REL="${FILE#"$ROOT"/}"
case "$REL" in
  .env|*/.env|*.joblib|backend/*|frontend/*|docs/referencia/*)
    echo "Bloqueado: $REL é protegido neste projeto (CLAUDE.md, regra 9). Peça a alteração a João Paulo." >&2
    exit 2 ;;
esac
exit 0
