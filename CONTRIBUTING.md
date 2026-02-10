# Contributing to ADHP

Thanks for your interest. This project is in early development and we welcome feedback.

## Ways to contribute

**Discussions** (best starting point): [GitHub Discussions](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions)

**Issues:** Bug reports, missing properties, edge cases.

**Pull requests:** Fixes to the demo, new example configs, documentation improvements. For spec changes, open a discussion first.

## Development setup

```bash
git clone https://github.com/StevenJohnson998/agent-data-handling-policy.git
cd agent-data-handling-policy/demo
docker compose up --build
bash tests/test_security.sh http://localhost:8910
```

## Code style

Python: PEP 8 · JSON: 2-space indent · Markdown: one sentence per line
