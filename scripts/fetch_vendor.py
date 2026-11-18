#!/usr/bin/env python3
"""Vendor-skill maintenance for skills/manifest.json.

Subcommands:
  fetch          (default)  Populate skills/vendor/<name>/ from the pinned SHAs.
  check-updates             Report which upstreams moved past their pinned SHA.
  update-refs               Rewrite skills/manifest.json refs to latest HEAD SHAs.

Every vendor skill records its exact upstream 40-char SHA in skills/manifest.json,
so fetching is deterministic and update checks are a plain ls-remote comparison.
"""

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "skills" / "manifest.json"
VENDOR = ROOT / "skills" / "vendor"


def load_skills() -> list[dict]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["skills"]


def save_skills(skills: list[dict]) -> None:
    MANIFEST.write_text(
        json.dumps({"skills": skills}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def vendor_skills(skills: list[dict]) -> list[dict]:
    return [s for s in skills if s.get("kind") == "vendor"]


def unique_repos(skills: list[dict]) -> dict[str, str]:
    """repo URL -> pinned ref (one ref per repo in the manifest)."""
    repos: dict[str, str] = {}
    for s in vendor_skills(skills):
        repos.setdefault(s["source"]["repo"], s["source"]["ref"])
    return repos


def head_sha(repo: str) -> str:
    out = subprocess.run(
        ["git", "ls-remote", repo, "HEAD"],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    ).stdout
    return out.split()[0]


def run(cmd, cwd=None):
    subprocess.run(
        cmd, check=True, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True
    )


def cmd_fetch() -> None:
    by_repo: dict[str, list[dict]] = {}
    for s in vendor_skills(load_skills()):
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


def cmd_check_updates() -> None:
    repos = unique_repos(load_skills())
    print(f"{'upstream':60s} {'pinned':14s} {'latest':14s}  status")
    print("-" * 100)
    outdated = 0
    for repo, pinned in repos.items():
        latest = head_sha(repo)
        label = repo.split("github.com/")[-1]
        if latest == pinned:
            print(f"{label:60s} {pinned[:12]:14s} {latest[:12]:14s}  up-to-date")
        else:
            outdated += 1
            print(f"{label:60s} {pinned[:12]:14s} {latest[:12]:14s}  OUTDATED")
            print(f"    {repo}/compare/{pinned}...{latest}")
    print("-" * 100)
    print(f"{len(repos) - outdated} up-to-date, {outdated} outdated")


def cmd_update_refs() -> None:
    skills = load_skills()
    repos = unique_repos(skills)

    updates: dict[str, str] = {}
    for repo, pinned in repos.items():
        latest = head_sha(repo)
        if latest != pinned:
            updates[repo] = latest

    if not updates:
        print("all refs already up-to-date; nothing to change")
        return

    for s in vendor_skills(skills):
        repo = s["source"]["repo"]
        if repo in updates:
            s["source"]["ref"] = updates[repo]

    save_skills(skills)
    for repo, sha in updates.items():
        print(f"updated {repo} -> {sha}")
    print("run `make vendor` to re-fetch vendor skills at the new refs")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="fetch_vendor.py", description=__doc__)
    parser.add_argument(
        "command",
        nargs="?",
        default="fetch",
        choices=["fetch", "check-updates", "update-refs"],
    )
    args = parser.parse_args(argv)
    if args.command == "fetch":
        cmd_fetch()
    elif args.command == "check-updates":
        cmd_check_updates()
    elif args.command == "update-refs":
        cmd_update_refs()


if __name__ == "__main__":
    main()
