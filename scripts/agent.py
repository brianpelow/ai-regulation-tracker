"""AI Regulation Tracker nightly agent."""

from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

REPO_ROOT = Path(__file__).parent.parent


def run() -> None:
    from tracker.sources import gather_all
    from tracker.synthesizer import generate_digest
    from tracker.publisher import get_issue_number, publish

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    github_token = os.environ.get("GITHUB_TOKEN", "")
    today = date.today()

    print(f"[agent] AI Regulation Tracker -- {today.isoformat()}")
    print(f"[agent] AI synthesis: {'enabled' if api_key else 'template mode'}")

    print("[agent] Gathering regulatory feeds...")
    current, horizon = gather_all()
    print(f"[agent] Found {len(current)} current items, {len(horizon)} horizon items")

    issue_number = get_issue_number(github_token) if github_token else 1

    print(f"[agent] Generating Issue #{issue_number}...")
    digest = generate_digest(current, horizon, api_key, issue_number)

    out_dir = REPO_ROOT / "archive"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"{today.isoformat()}-issue-{issue_number:04d}.md"
    out_file.write_text(digest, encoding="utf-8")
    print(f"[agent] Saved to {out_file}")

    if github_token:
        print("[agent] Publishing to GitHub Discussions...")
        ok = publish(digest, issue_number, github_token)
        if not ok:
            print("[agent] Publish failed -- digest saved to archive only")
    else:
        print("[agent] No GITHUB_TOKEN -- skipping publish")

    print("[agent] Done.")
    print("\n--- DIGEST PREVIEW ---")
    print(digest[:600] + "..." if len(digest) > 600 else digest)


if __name__ == "__main__":
    run()