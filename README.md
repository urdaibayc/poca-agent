# my-agent

A personal opencode-native multi-agent coding workflow. A planner skill writes a
validated plan; an executor skill dispatches each task to a worker subagent
(`worker-private` for sensitive work, `worker-free` for clearly non-sensitive
work). Model tiering: your high-reasoning model orchestrates, cheap models execute.

## Layout

```
skills/
  manifest.json     # skill catalog (custom + vendor), and vendor sources with pinned SHAs
  custom/           # my adapted skills (planner, executor) — committed
  vendor/           # third-party skills — fetched, gitignored
  licenses/         # third-party license texts — committed
mcp/
  server.py         # FastMCP server: list_development_skills, list_opencode_models
  pyproject.toml    # mcp dependency
```

## Setup

```sh
make mcp      # requires uv: curl -LsSf https://astral.sh/uv/install.sh | sh
make vendor   # fetch third-party skills at their pinned SHAs
```

`make vendor` is deterministic: each skill's `source.ref` in `skills/manifest.json`
is an exact 40-char commit SHA.

## Wiring (dotfiles)

The skills and workers are wired from `~/.config/opencode/opencode.jsonc` (managed
by GNU Stow in the dotfiles repo). It points the `skills` array at
`~/code/my-agent/skills/{custom,vendor}`, defines `worker-private`/`worker-free`
as inline agents, and points the `my-agent-skills` MCP server at `mcp/.venv`.
This repo never symlinks into `~/.config/opencode/`.
