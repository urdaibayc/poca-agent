#!/usr/bin/env python3
"""FastMCP server exposing the my-agent skill catalog and opencode model resolver.

The planner and executor skills call these tools. Skills live in this repo's
skills/ directory (custom/ committed, vendor/ fetched via scripts/fetch_vendor.py);
this server reads skills/manifest.json for the catalog and resolves model names to
exact opencode ids.
"""

import json
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-agent-skills")

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
MANIFEST_PATH = SKILLS_DIR / "manifest.json"


@mcp.tool()
def list_development_skills() -> str:
    """Reads skills/manifest.json and returns all development skills (group 'build',
    excluding 'executor') with their summaries, offerWhen criteria and installed state.
    """
    if not MANIFEST_PATH.exists():
        return json.dumps({"error": f"Manifest not found at {MANIFEST_PATH}"})

    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    dev_skills = []
    for skill in data.get("skills", []):
        if skill.get("group") == "build" and skill.get("name") != "executor":
            skill_path = SKILLS_DIR / skill.get("path", "") / "SKILL.md"
            dev_skills.append(
                {
                    "name": skill["name"],
                    "summary": skill.get("summary", ""),
                    "offerWhen": skill.get("offerWhen", ""),
                    "author": skill.get("author", ""),
                    "installed": skill_path.exists(),
                }
            )
    return json.dumps(
        {"skills_root": str(SKILLS_DIR), "development_skills": dev_skills},
        indent=2,
        ensure_ascii=False,
    )


@mcp.tool()
def list_opencode_models(search_filter: str = "") -> str:
    """Lists exact model IDs (<provider>/<model-id>) available in opencode (including
    opencode zen). Always call this to resolve informal model names before writing a plan
    or dispatching a worker.
    """
    try:
        res = subprocess.run(
            ["opencode", "models"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        if search_filter:
            q = search_filter.lower()
            lines = [line for line in lines if q in line.lower()]
        return "\n".join(lines) if lines else "No matching models found."
    except Exception as exc:
        return f"Error running 'opencode models': {exc}"


if __name__ == "__main__":
    mcp.run()
