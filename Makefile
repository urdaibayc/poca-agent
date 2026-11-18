.PHONY: vendor mcp check-updates update-refs clean

## Fetch third-party vendor skills at their pinned SHAs (see skills/manifest.json).
vendor:
	python3 scripts/fetch_vendor.py fetch

## Create/lock the MCP runtime venv (mcp/.venv) from mcp/pyproject.toml.
mcp:
	cd mcp && uv sync --frozen || cd mcp && uv sync

## Report which upstreams moved past their pinned SHA, with GitHub compare URLs.
check-updates:
	python3 scripts/fetch_vendor.py check-updates

## Bump skills/manifest.json refs to the latest upstream HEAD SHAs.
update-refs:
	python3 scripts/fetch_vendor.py update-refs

## Remove fetched vendor skills and the MCP venv.
clean:
	rm -rf skills/vendor/* mcp/.venv
