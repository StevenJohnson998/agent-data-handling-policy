"""ADHP SDK Test GUI — simple web interface for testing compliance checks.

Serves a single HTML page on port 9199 that lets testers:
- Select a target test server
- Configure client requirements
- Run compliance checks and see results
- View raw JSON exchange

Also acts as an API proxy to avoid browser CORS issues.

Usage:
    source ~/venvs/adhp-sdk/bin/activate
    python test-gui.py
"""

import json

import httpx
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ADHP SDK Test GUI</title>
<style>
  :root { --pass: #22c55e; --fail: #ef4444; --bg: #0f172a; --card: #1e293b; --border: #334155; --text: #e2e8f0; --muted: #94a3b8; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace; background: var(--bg); color: var(--text); min-height: 100vh; padding: 1rem; }
  h1 { font-size: 1.5rem; margin-bottom: 0.25rem; }
  .subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 1.5rem; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; max-width: 1200px; margin: 0 auto; }
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; }
  .card h2 { font-size: 1rem; margin-bottom: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; font-size: 0.75rem; }
  label { display: block; font-size: 0.85rem; color: var(--muted); margin-bottom: 0.25rem; margin-top: 0.75rem; }
  select, input[type="text"] { width: 100%; padding: 0.5rem; background: var(--bg); border: 1px solid var(--border); border-radius: 4px; color: var(--text); font-size: 0.9rem; }
  .checkbox-row { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem; }
  .checkbox-row input { width: auto; }
  .checkbox-row label { margin: 0; }
  button { background: #3b82f6; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 6px; font-size: 1rem; cursor: pointer; margin-top: 1rem; width: 100%; font-weight: 600; }
  button:hover { background: #2563eb; }
  button:disabled { background: #475569; cursor: not-allowed; }
  .result-box { margin-top: 1rem; padding: 1rem; border-radius: 6px; font-size: 0.9rem; }
  .result-pass { background: #052e16; border: 1px solid var(--pass); }
  .result-fail { background: #450a0a; border: 1px solid var(--fail); }
  .result-title { font-size: 1.1rem; font-weight: bold; margin-bottom: 0.5rem; }
  .check-item { padding: 0.25rem 0; font-size: 0.85rem; }
  .check-pass { color: var(--pass); }
  .check-fail { color: var(--fail); }
  .json-box { background: var(--bg); border: 1px solid var(--border); border-radius: 4px; padding: 0.75rem; font-family: monospace; font-size: 0.75rem; white-space: pre-wrap; word-break: break-all; max-height: 300px; overflow-y: auto; margin-top: 0.75rem; color: var(--muted); }
  .full-width { grid-column: 1 / -1; }
  .server-info { font-size: 0.8rem; color: var(--muted); margin-top: 0.25rem; }
  @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div style="max-width:1200px;margin:0 auto">
  <h1>ADHP SDK Test GUI</h1>
  <p class="subtitle">Agent Data Handling Policy — compliance checker test harness</p>

  <div class="grid">
    <!-- Left: Server Selection + Requirements -->
    <div class="card">
      <h2>Target Server</h2>
      <select id="server">
        <option value="9100">Healthcare Server :9100 (strict, GDPR+HIPAA, DE)</option>
        <option value="9101">Finance Server :9101 (strict, GDPR+AI_ACT_EU, DE+FR)</option>
        <option value="9102">Open Agent :9102 (open, no restrictions)</option>
        <option value="9103">EU Standard :9103 (standard, GDPR, DE+FR+NL)</option>
      </select>
      <div id="server-adhp" class="server-info">Select a server and click "Fetch Policy" to see its ADHP declaration</div>
      <button onclick="fetchPolicy()" style="background:#6366f1;margin-top:0.5rem">Fetch Policy</button>

      <h2 style="margin-top:1.5rem">Client Requirements</h2>

      <label>Minimum Level</label>
      <select id="minLevel">
        <option value="open">open (0)</option>
        <option value="standard" selected>standard (1)</option>
        <option value="sensitive">sensitive (2)</option>
        <option value="strict">strict (3)</option>
        <option value="zero-trace">zero-trace (4)</option>
      </select>

      <label>Required Compliance (comma-separated)</label>
      <input type="text" id="compliance" placeholder="e.g. GDPR,HIPAA">

      <label>Accepted Jurisdictions (comma-separated ISO codes)</label>
      <input type="text" id="jurisdictions" placeholder="e.g. DE,FR,NL">

      <label>Max Retention</label>
      <select id="maxRetention">
        <option value="">No requirement</option>
        <option value="none">none</option>
        <option value="request">request</option>
        <option value="session">session</option>
        <option value="24h">24h</option>
        <option value="7d">7d</option>
        <option value="30d">30d</option>
        <option value="unlimited">unlimited</option>
      </select>

      <div class="checkbox-row">
        <input type="checkbox" id="trainingOptOut">
        <label for="trainingOptOut">Require training opt-out</label>
      </div>
      <div class="checkbox-row">
        <input type="checkbox" id="noThirdParty">
        <label for="noThirdParty">Require no third-party sharing</label>
      </div>
      <div class="checkbox-row">
        <input type="checkbox" id="noContentLogging">
        <label for="noContentLogging">Require content logging opt-out</label>
      </div>

      <button id="checkBtn" onclick="runCheck()">Check Compliance</button>
    </div>

    <!-- Right: Results -->
    <div class="card">
      <h2>Result</h2>
      <div id="result">
        <p style="color:var(--muted)">Click "Check Compliance" to run a check against the selected server.</p>
      </div>

      <h2 style="margin-top:1.5rem">Raw JSON Exchange</h2>
      <div>
        <label>Request (client requirements)</label>
        <div id="jsonRequest" class="json-box">—</div>
        <label>Response (server ADHP)</label>
        <div id="jsonResponse" class="json-box">—</div>
      </div>
    </div>
  </div>
</div>

<script>
function getRequirements() {
  const comp = document.getElementById('compliance').value.trim();
  const jur = document.getElementById('jurisdictions').value.trim();
  const maxRet = document.getElementById('maxRetention').value;
  return {
    min_level: document.getElementById('minLevel').value,
    require_compliance: comp ? comp.split(',').map(s => s.trim()).filter(Boolean) : [],
    accepted_jurisdictions: jur ? jur.split(',').map(s => s.trim().toUpperCase()).filter(Boolean) : [],
    require_training_opt_out: document.getElementById('trainingOptOut').checked,
    require_no_third_party: document.getElementById('noThirdParty').checked,
    require_content_logging_opt_out: document.getElementById('noContentLogging').checked,
    max_retention: maxRet || null,
  };
}

async function fetchPolicy() {
  const port = document.getElementById('server').value;
  const el = document.getElementById('server-adhp');
  el.textContent = 'Fetching...';
  try {
    const resp = await fetch(`/api/adhp?port=${port}`);
    const data = await resp.json();
    el.textContent = JSON.stringify(data, null, 2);
    el.style.whiteSpace = 'pre-wrap';
    el.style.fontFamily = 'monospace';
    el.style.fontSize = '0.75rem';
  } catch (e) {
    el.textContent = 'Error: ' + e.message;
  }
}

async function runCheck() {
  const port = document.getElementById('server').value;
  const requirements = getRequirements();
  const btn = document.getElementById('checkBtn');

  document.getElementById('jsonRequest').textContent = JSON.stringify(requirements, null, 2);
  btn.disabled = true;
  btn.textContent = 'Checking...';

  try {
    const resp = await fetch('/api/check', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ port, requirements }),
    });
    const data = await resp.json();

    document.getElementById('jsonResponse').textContent = JSON.stringify(data, null, 2);

    const resultEl = document.getElementById('result');
    const compliant = data.compliant;
    let html = `<div class="result-box ${compliant ? 'result-pass' : 'result-fail'}">`;
    html += `<div class="result-title">${compliant ? 'PASS' : 'FAIL'} — ${compliant ? 'Server meets all requirements' : 'Server does NOT meet requirements'}</div>`;
    if (data.checks) {
      for (const c of data.checks) {
        const cls = c.passed ? 'check-pass' : 'check-fail';
        const icon = c.passed ? 'PASS' : 'FAIL';
        html += `<div class="check-item ${cls}">[${icon}] ${c.name}: ${c.reason}</div>`;
      }
    }
    html += '</div>';
    resultEl.innerHTML = html;
  } catch (e) {
    document.getElementById('result').innerHTML = `<div class="result-box result-fail"><div class="result-title">Error</div>${e.message}</div>`;
    document.getElementById('jsonResponse').textContent = 'Error: ' + e.message;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Check Compliance';
  }
}
</script>
</body>
</html>"""


async def index(request: Request) -> HTMLResponse:
    return HTMLResponse(HTML_PAGE)


async def api_adhp(request: Request) -> JSONResponse:
    """Proxy: fetch ADHP from a test server."""
    port = request.query_params.get("port", "9100")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"http://127.0.0.1:{port}/adhp")
            return JSONResponse(resp.json())
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=502)


async def api_check(request: Request) -> JSONResponse:
    """Run compliance check: fetch server ADHP, apply client requirements."""
    body = await request.json()
    port = body.get("port", "9100")
    requirements = body.get("requirements", {})

    # Fetch server ADHP
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(
                f"http://127.0.0.1:{port}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-03-26",
                        "clientInfo": {"name": "Test GUI", "version": "0.1"},
                    },
                },
            )
            mcp_data = resp.json()
    except Exception as e:
        return JSONResponse({"error": f"Cannot reach server on port {port}: {e}"}, status_code=502)

    adhp_data = mcp_data.get("result", {}).get("capabilities", {}).get("adhp")

    # Run check
    from adhp.checker import check_compliance
    from adhp.models import ADHPClientRequirements

    req = ADHPClientRequirements(**requirements)
    result = check_compliance(req, adhp_data)

    return JSONResponse({
        "compliant": result.compliant,
        "checks": [{"name": c.name, "passed": c.passed, "reason": c.reason} for c in result.checks],
        "server_adhp": adhp_data,
    })


app = Starlette(routes=[
    Route("/", index),
    Route("/api/adhp", api_adhp),
    Route("/api/check", api_check, methods=["POST"]),
])

if __name__ == "__main__":
    print("\n  ADHP SDK Test GUI")
    print("  http://localhost:9199\n")
    uvicorn.run(app, host="0.0.0.0", port=9199)
