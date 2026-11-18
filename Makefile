.PHONY: vendor mcp

## Fetch third-party vendor skills at their pinned SHAs (see skills/manifest.json).
vendor:
	python3 scripts/fetch_vendor.py

## Create/lock the MCP runtime venv (mcp/.venv) from mcp/pyproject.toml.
mcp:
	cd mcp && uv sync
