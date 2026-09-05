# Local Chat Agent (Ollama + Web Search)

A fully local agent: the LLM runs on your machine via Ollama, and it can
search the web (DuckDuckGo, no API key needed) whenever it decides it needs to.

## 1. Install Ollama (the local LLM runtime)
Download from https://ollama.com and install it, then pull a model that
supports tool calling:

```bash
ollama pull llama3.1
```

(Other tool-capable options: `qwen2.5`, `mistral-nemo`. Bigger models reason
about *when* to call tools more reliably but need more RAM/VRAM.)

Make sure Ollama is running in the background (it usually starts a local
server automatically on `http://localhost:11434`).

## 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

## 3. Run the agent

```bash
python agent.py
```

Chat normally. Ask something like "what's the weather in Tokyo right now"
or "who won the last F1 race" — you'll see it print `[tool call] web_search(...)`
before answering, which means it decided on its own to search.

## How it works (the short version)

- `messages` is just a growing list of `{role, content}` dicts — the entire
  conversation history, including tool results.
- `TOOLS` is a JSON schema describing what functions exist and what
  arguments they take. This is sent to the model on every call so it knows
  what's available.
- When the model wants to use a tool, it doesn't run any code itself — it
  just replies with a structured `tool_calls` request. **Your code** is what
  actually executes `web_search()`, then appends the result back into
  `messages` as a `role: "tool"` message.
- The model is called again with that result in context, and either answers
  or calls another tool. This request → tool → request cycle is the entire
  "agent loop."

## Running with Docker (recommended for portability)

This runs Ollama and the agent as two containers, wired together with
`docker-compose`. Models are stored in a persistent volume so you don't
re-download them on every rebuild.

```bash
# 1. Start Ollama in the background
docker compose up -d ollama

# 2. Pull a tool-capable model into the running Ollama container
docker exec -it ollama ollama pull llama3.1

# 3. Build and run the agent interactively
docker compose run --rm agent
```

`docker compose run --rm agent` (rather than `up`) is used because the
agent is an interactive terminal chat — this attaches your terminal to it
properly and removes the container when you exit.

To stop everything:

```bash
docker compose down
```

Your pulled models persist in the `ollama_data` volume even after `down`,
so you won't need to re-pull them next time.

**Notes:**
- To use a different model, change `OLLAMA_MODEL` in `docker-compose.yml`
  and `docker exec -it ollama ollama pull <model>`.
- GPU acceleration: uncomment the `deploy.resources` block in
  `docker-compose.yml` (requires the NVIDIA Container Toolkit on the host).
  Without a GPU, Ollama runs on CPU — fine for small models, slow for large ones.

## Where to go from here

- **Add more tools**: e.g. a calculator, file reader, or a Google Custom
  Search API call instead of DuckDuckGo (needs an API key + Custom Search
  Engine ID from https://programmablesearchengine.google.com/).
- **Add memory**: persist `messages` to a file/SQLite between runs so the
  agent remembers past conversations.
- **Add a UI**: wrap `run_agent_turn()` in a simple Flask/Gradio app instead
  of the terminal loop.
- **Swap models**: any Ollama model that supports `tools` will drop in by
  changing the `MODEL` variable.
