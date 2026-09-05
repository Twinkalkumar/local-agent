FROM python:3.11-slim

WORKDIR /app

# System deps (kept minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent.py .

# Talks to the "ollama" service defined in docker-compose.yml by default.
# Override with -e OLLAMA_HOST=... if running standalone.
ENV OLLAMA_HOST=http://ollama:11434
ENV OLLAMA_MODEL=llama3.1

# Interactive terminal chat needs stdin attached: docker compose run agent
CMD ["python", "-u", "agent.py"]
