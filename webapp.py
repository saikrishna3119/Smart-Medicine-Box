# ============================================================
# webapp.py — Flask Web Control Panel
# Access from any browser on the local network
# ============================================================

from flask import Flask, request, jsonify, render_template_string
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Injected at runtime by main.py
_open_box_fn   = None
_speak_fn      = None


def init_webapp(open_box_fn, speak_fn):
    """Inject dependencies before starting the server."""
    global _open_box_fn, _speak_fn
    _open_box_fn = open_box_fn
    _speak_fn    = speak_fn


# ── HTML Template ─────────────────────────────────────────────
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Smart Medicine Box</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', sans-serif;
      background: linear-gradient(135deg, #e0f7fa, #b2ebf2);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 30px 16px;
    }
    h1 {
      font-size: 2rem;
      color: #00695c;
      margin-bottom: 6px;
      text-align: center;
    }
    p.sub {
      color: #555;
      margin-bottom: 30px;
      font-size: 1rem;
      text-align: center;
    }
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      width: 100%;
      max-width: 480px;
    }
    .card {
      background: white;
      border-radius: 16px;
      padding: 28px 20px;
      text-align: center;
      box-shadow: 0 4px 20px rgba(0,0,0,0.1);
      transition: transform 0.15s;
    }
    .card:hover { transform: translateY(-4px); }
    .card .icon { font-size: 3rem; margin-bottom: 12px; }
    .card h2 { font-size: 1.1rem; color: #333; margin-bottom: 8px; }
    .card .medicine-name { font-size: 0.85rem; color: #888; margin-bottom: 16px; }
    .btn {
      background: #00897b;
      color: white;
      border: none;
      border-radius: 10px;
      padding: 12px 24px;
      font-size: 1rem;
      cursor: pointer;
      width: 100%;
      transition: background 0.2s;
    }
    .btn:hover   { background: #00695c; }
    .btn:active  { background: #004d40; transform: scale(0.97); }
    .btn.loading { background: #aaa; pointer-events: none; }
    #status {
      margin-top: 24px;
      padding: 14px 24px;
      background: white;
      border-radius: 12px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.08);
      font-size: 1rem;
      color: #333;
      max-width: 480px;
      width: 100%;
      text-align: center;
      min-height: 48px;
    }
    #log {
      margin-top: 20px;
      max-width: 480px;
      width: 100%;
      background: white;
      border-radius: 12px;
      padding: 16px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    }
    #log h3 { color: #00695c; margin-bottom: 10px; font-size: 0.95rem; }
    #log-entries { font-size: 0.85rem; color: #444; line-height: 1.7; }
    footer {
      margin-top: 30px;
      font-size: 0.8rem;
      color: #888;
    }
  </style>
</head>
<body>
  <h1>💊 Smart Medicine Box</h1>
  <p class="sub">Tap a button to open a compartment</p>

  <div class="grid">
    <div class="card">
      <div class="icon">🌅</div>
      <h2>Box 1</h2>
      <div class="medicine-name">Morning</div>
      <button class="btn" onclick="openBox(1, this)">Open Box 1</button>
    </div>
    <div class="card">
      <div class="icon">☀️</div>
      <h2>Box 2</h2>
      <div class="medicine-name">Afternoon</div>
      <button class="btn" onclick="openBox(2, this)">Open Box 2</button>
    </div>
    <div class="card">
      <div class="icon">🌙</div>
      <h2>Box 3</h2>
      <div class="medicine-name">Evening</div>
      <button class="btn" onclick="openBox(3, this)">Open Box 3</button>
    </div>
    <div class="card">
      <div class="icon">⭐</div>
      <h2>Box 4</h2>
      <div class="medicine-name">Extra</div>
      <button class="btn" onclick="openBox(4, this)">Open Box 4</button>
    </div>
  </div>

  <div id="status">Ready. Select a compartment above.</div>

  <div id="log">
    <h3>📋 Recent Activity</h3>
    <div id="log-entries">No recent activity.</div>
  </div>

  <footer>Smart Medicine Box — Raspberry Pi 5</footer>

  <script>
    const logEntries = [];

    async function openBox(boxNum, btn) {
      btn.textContent = 'Opening…';
      btn.classList.add('loading');
      document.getElementById('status').textContent =
        `Opening compartment ${boxNum}…`;

      try {
        const res = await fetch(`/open_box?box=${boxNum}`);
        const data = await res.json();

        document.getElementById('status').textContent =
          data.success
            ? `✅ ${data.message}`
            : `❌ ${data.message}`;

        const now = new Date().toLocaleTimeString();
        logEntries.unshift(`${now} — Box ${boxNum} opened`);
        if (logEntries.length > 10) logEntries.pop();
        document.getElementById('log-entries').innerHTML =
          logEntries.join('<br>');

      } catch (err) {
        document.getElementById('status').textContent =
          '❌ Network error. Is the server running?';
      } finally {
        btn.textContent = `Open Box ${boxNum}`;
        btn.classList.remove('loading');
      }
    }
  </script>
</body>
</html>
"""


# ── Routes ───────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/open_box")
def open_box_endpoint():
    box_param = request.args.get("box", "")
    try:
        box = int(box_param)
        if box not in (1, 2, 3, 4):
            raise ValueError("Out of range")
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid box number (1–4)"}), 400

    try:
        logger.info(f"Web request: open box {box}")
        if _speak_fn:
            _speak_fn(f"Web command received. Opening compartment {box}.")
        if _open_box_fn:
            _open_box_fn(box)
        return jsonify({"success": True, "message": f"Compartment {box} opened."})
    except Exception as e:
        logger.error(f"Web open_box error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/status")
def status():
    """Health-check endpoint."""
    return jsonify({"status": "ok", "message": "Smart Medicine Box is running."})


def run_webapp(host, port):
    """Start Flask development server (non-debug for production use)."""
    app.run(host=host, port=port, debug=False, use_reloader=False)
