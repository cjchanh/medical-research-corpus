#!/bin/sh
# Wait for the Ollama service, ensure the embed model is present, then run the command.
# POSIX sh (python:slim has /bin/sh + python3, not necessarily bash or curl).
set -eu

OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
MODEL="${EMBED_MODEL:-nomic-embed-text}"

echo ">> waiting for Ollama at ${OLLAMA_URL} ..."
i=0
while [ "$i" -lt 90 ]; do
  if python3 -c "import urllib.request; urllib.request.urlopen('${OLLAMA_URL}/api/tags', timeout=2)" 2>/dev/null; then
    break
  fi
  i=$((i + 1))
  sleep 2
done

echo ">> ensuring embed model '${MODEL}' is present (first run pulls it, ~275MB) ..."
python3 - "$OLLAMA_URL" "$MODEL" <<'PY'
import json, sys, urllib.request
url, model = sys.argv[1], sys.argv[2]
try:
    req = urllib.request.Request(
        url + "/api/pull",
        data=json.dumps({"name": model}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=1800) as r:
        for _ in r:  # drain the streaming pull to completion
            pass
    print(">> embed model ready")
except Exception as exc:  # non-fatal: embeddings.py will try on demand
    print(">> warn: could not pre-pull model (%s)" % exc, file=sys.stderr)
PY

exec "$@"
