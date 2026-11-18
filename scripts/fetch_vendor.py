#!/usr/bin/env python3
"""Populate skills/vendor/<name>/ from the pinned upstream SHAs in skills/manifest.json.

Each vendor skill is fetched with a blobless sparse clone of its upstream repo at
the exact 40-char ref recorded in the manifest, so `make vendor` is deterministic.
"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "skills" / "manifest.json"
VENDOR = ROOT / "skills" / "vendor"


def run(cmd, cwd=None):
    subprocess.run(cmd, check=True, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)


def main() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    vendor_skills = [s for s in data["skills"] if s.get("kind") == "vendor"]

    by_repo: dict[str, list[dict]] = {}
    for s in vendor_skills:
        by_repo.setdefault(s["source"]["repo"], []).append(s)

    VENDOR.mkdir(parents=True, exist_ok=True)

    for repo, skills in by_repo.items():
        ref = skills[0]["source"]["ref"]
        paths = sorted({s["source"]["path"] for s in skills})

        with tempfile.TemporaryDirectory(prefix="my-agent-vendor-") as tmp:
            run(["git", "init", "-q", tmp])
            run(["git", "-C", tmp, "remote", "add", "origin", repo])
            run(["git", "-C", tmp, "fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", ref])
            run(["git", "-C", tmp, "sparse-checkout", "init", "--cone"])
            run(["git", "-C", tmp, "sparse-checkout", "set", "--no-cone", *paths])
            run(["git", "-C", tmp, "checkout", "-q", ref])

            for s in skills:
                src = Path(tmp) / s["source"]["path"]
                if not src.exists():
                    raise SystemExit(
                        f"fetch failed: {s['name']}: {s['source']['path']} not found in {repo} @ {ref}"
                    )
                dest = VENDOR / s["name"]
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(src, dest)
                print(f"  {s['name']:32s} <- {s['source']['repo'].split('/')[-1]} @ {ref[:12]} :: {s['source']['path']}")


if __name__ == "__main__":
    main()
