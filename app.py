"""
Web UI for the local agent — Flask backend.

Reuses the exact same agent loop from agent.py (client, tools, run_agent_turn).
The browser just POSTs a message to /api/chat and gets the final text answer;
all the tool-calling happens server-side, same as the terminal version.
"""

from flask import Flask, render_template, request, jsonify

from agent import (
    client,
    MODEL,
    OLLAMA_HOST,
    SYSTEM_PROMPT,
    run_agent_turn,
    wait_for_ollama,
)

app = Flask(__name__)

# Single in-memory conversation (fine for a local, single-user tool).
# Swap for a per-session store if you want multi-user support later.
conversation = [{"role": "system", "content": SYSTEM_PROMPT}]


@app.route("/")
def index():
    return render_template("index.html", model=MODEL)


@app.route("/api/status")
def status():
    try:
        client.list()
        return jsonify({"connected": True, "model": MODEL, "host": OLLAMA_HOST})
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)}), 503


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    conversation.append({"role": "user", "content": user_message})
    try:
        answer = run_agent_turn(conversation)
    except Exception as e:
        # Don't leave a dangling user message in history if the call failed
        conversation.pop()
        return jsonify({"error": str(e)}), 500

    return jsonify({"reply": answer})


@app.route("/api/reset", methods=["POST"])
def reset():
    global conversation
    conversation = [{"role": "system", "content": SYSTEM_PROMPT}]
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    wait_for_ollama()
    app.run(host="0.0.0.0", port=5000)
