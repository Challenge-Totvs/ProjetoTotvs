#!/bin/bash
# Stop: o turno só termina se os testes passam. Desligue com SKIP_STOP_PYTEST=1. Sem jq: usa Python.
cat >/dev/null
[ "$SKIP_STOP_PYTEST" = "1" ] && exit 0
DIR="$CLAUDE_PROJECT_DIR/analise-service"
[ -d "$DIR/tests" ] || exit 0
PY="$DIR/.venv/bin/python"
[ -x "$PY" ] || PY="$DIR/.venv/Scripts/python.exe"
[ -x "$PY" ] || PY=$(command -v python3 || command -v python || command -v py)
[ -z "$PY" ] && { echo "stop-pytest: Python não encontrado." >&2; exit 0; }
cd "$DIR" || exit 0
OUT=$("$PY" -m pytest -q -x 2>&1); RC=$?
# 5 = nenhum teste coletado; "No module named pytest" = sem venv: avisa, não trava o turno
if echo "$OUT" | grep -q "No module named pytest"; then
  echo "stop-pytest: pytest não encontrado em $PY (crie a .venv)." >&2
  exit 0
fi
[ $RC -eq 5 ] && exit 0
if [ $RC -ne 0 ]; then
  printf '%s' "$OUT" | tail -25 | "$PY" -c 'import sys,json
t=sys.stdin.read()
print(json.dumps({"decision":"block","reason":"pytest falhou. Corrija antes de encerrar. Ultimas linhas:\n"+t}))'
fi
exit 0
