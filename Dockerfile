# medical-research-corpus engine — sovereign local medical-evidence retrieval.
# Runs alongside an Ollama service via docker-compose (see docker-compose.yml).
FROM python:3.12-slim

WORKDIR /app

# The engine is Python stdlib-only; matplotlib is the lone dependency (figure script).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x docker-entrypoint.sh

# Reach the Ollama service over the compose network (overridable).
ENV OLLAMA_URL=http://ollama:11434

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python3", "-c", "print('medical-research-corpus engine ready.\\n  build a corpus:  docker compose run --rm engine python3 seed.py \\\"<condition>\\\"\\n  ask it:         docker compose run --rm engine python3 grounded.py \\\"<question>\\\"')"]
