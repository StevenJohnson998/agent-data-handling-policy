# ADHP Demo — MCP Handshake with ADHP Extension

A working demo of ADHP extending the MCP protocol. The server responds to MCP `initialize` requests with data handling declarations in the capabilities object.

**Core concept:** a client checks an agent's privacy policy before sending any data.

## Quick start

### 1. Run the server

```bash
cd demo
docker compose up --build -d
```

### 2. Test with curl

```bash
curl -s -X POST http://localhost:8910/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "capabilities": {},
      "clientInfo": {"name": "curl-test", "version": "1.0"}
    }
  }' | python3 -m json.tool
```

### 3. Test with the client script

```bash
cd demo/client
pip install -r requirements.txt

# Basic check
python client.py --url http://localhost:8910/mcp

# Strict requirements
python client.py --url http://localhost:8910/mcp \
  --min-level strict \
  --require-compliance GDPR HIPAA \
  --no-third-party \
  --require-jurisdiction DE

# Requirement the server can't meet → FAIL
python client.py --url http://localhost:8910/mcp --min-level zero-trace
```

## Configuration

Edit `server/adhp-config.json` to change the server's ADHP declaration. Restart after editing.

See `../examples/adhp-configs/` for sample configs (healthcare, finance, open-source, zero-trace).

## Security

| Protection | Layer |
|-----------|-------|
| Rate limiting (10 req/min per IP) | Application |
| Body size limit (4KB) | Application |
| Method whitelist (initialize, ping only) | Application |
| No Swagger/OpenAPI exposed | Application |
| Read-only filesystem, no capabilities | Docker |
| Non-root user, 128MB memory limit | Docker |
| Localhost binding only | Docker + Caddy |

Run tests: `bash tests/test_security.sh http://localhost:8910`

## How it works

Follows [MCP spec (2025-03-26)](https://spec.modelcontextprotocol.io/specification/2025-03-26/basic/lifecycle/). ADHP adds an `adhp` key inside the server's `capabilities` object — a protocol extension, not a modification.
