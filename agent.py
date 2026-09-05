"""
Local AI Agent — chat + web search, fully offline LLM via Ollama.

Architecture:
  User -> messages[] -> Ollama model -> (text answer) OR (tool_call request)
  If tool_call: run the real Python function -> feed result back into messages[]
  -> call model again -> repeat until it gives a plain text answer.

This is the same "agent loop" pattern used by every agent framework,
just written out explicitly so you can see and modify every step.
"""

import ollama
from duckduckgo_search import DDGS

# ---------------------------------------------------------------------------
# 1. CONFIG
# ---------------------------------------------------------------------------
# Model must support "tool calling" in Ollama. Good options (pull first):
#   ollama pull llama3.1
#   ollama pull qwen2.5
#   ollama pull mistral-nemo
MODEL = "llama3.1"

SYSTEM_PROMPT = (
    "You are a helpful local assistant. "
    "Use the web_search tool whenever the user asks about current events, "
    "facts you are unsure of, prices, dates, or anything time-sensitive. "
    "Otherwise, just answer directly and concisely."
)

# ---------------------------------------------------------------------------
# 2. TOOL IMPLEMENTATION (the actual Python function that does the work)
# ---------------------------------------------------------------------------
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web (DuckDuckGo, no API key needed) and return results as text."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "No results found."
        lines = [f"- {r['title']}: {r['body']} (source: {r['href']})" for r in results]
        return "\n".join(lines)
    except Exception as e:
        return f"Search failed: {e}"


# ---------------------------------------------------------------------------
# 3. TOOL SCHEMA (this is what tells the MODEL the tool exists and how to call it)
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for current, real-time, or factual information "
                "the model may not know or that changes over time."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "How many results to fetch (default 5).",
                    },
                },
                "required": ["query"],
            },
        },
    }
]

# Map from tool name (string) -> actual Python function to call
AVAILABLE_FUNCTIONS = {
    "web_search": web_search,
}


# ---------------------------------------------------------------------------
# 4. THE AGENT LOOP
# ---------------------------------------------------------------------------
def run_agent_turn(messages: list) -> str:
    """Send messages to the model, resolve any tool calls, return final text answer."""
    response = ollama.chat(model=MODEL, messages=messages, tools=TOOLS)
    msg = response["message"]
    messages.append(msg)

    # Keep resolving tool calls until the model gives a plain answer
    while msg.get("tool_calls"):
        for call in msg["tool_calls"]:
            fn_name = call["function"]["name"]
            fn_args = call["function"]["arguments"]
            print(f"  [tool call] {fn_name}({fn_args})")

            fn = AVAILABLE_FUNCTIONS.get(fn_name)
            result = fn(**fn_args) if fn else f"Unknown tool: {fn_name}"

            messages.append({"role": "tool", "content": result})

        response = ollama.chat(model=MODEL, messages=messages, tools=TOOLS)
        msg = response["message"]
        messages.append(msg)

    return msg["content"]


def main():
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print(f"Local agent ready (model: {MODEL}). Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})
        answer = run_agent_turn(messages)
        print(f"\nAgent: {answer}\n")


if __name__ == "__main__":
    main()
