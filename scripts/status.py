#!/usr/bin/env python3
"""Build the factory status page: every project, its stage, play link, CI and activity.

Reads public GitHub data only (no secrets needed beyond the workflow's read token) and
writes a single static HTML page. Every value shown comes from repositories that agents
can edit, so all of it is HTML-escaped. Stdlib only.

Usage: status.py --owner ORG --out DIR   (GH_TOKEN optional; raises the API rate limit)
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import pathlib
import sys
import urllib.request

API = "https://api.github.com"
STAGES = ("experiment", "active", "archived")


def get(path: str) -> object:
    req = urllib.request.Request(f"{API}/{path}", headers={
        "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "factory-status"})
    if token := os.environ.get("GH_TOKEN"):
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def collect(owner: str) -> list[dict]:
    projects = []
    for repo in get(f"orgs/{owner}/repos?type=public&per_page=100"):
        topics = repo.get("topics") or []
        if "factory" not in topics:
            continue
        stage = "archived" if repo.get("archived") else next(
            (t.removeprefix("stage-") for t in topics if t.startswith("stage-")), "unknown")
        runs = get(f"repos/{owner}/{repo['name']}/actions/runs?branch=main&per_page=20")
        ci = next((r for r in runs.get("workflow_runs", []) if r.get("name") == "ci"), None)
        projects.append({
            "name": repo["name"],
            "url": repo["html_url"],
            "play": repo.get("homepage") or "",
            "description": repo.get("description") or "",
            "stage": stage,
            "ci": (ci or {}).get("conclusion") or (ci or {}).get("status") or "none",
            "ci_url": (ci or {}).get("html_url") or "",
            "pushed": (repo.get("pushed_at") or "")[:10],
        })
    order = {s: i for i, s in enumerate(STAGES)}
    return sorted(projects, key=lambda p: (order.get(p["stage"], 9), p["name"]))


def render(owner: str, projects: list[dict], generated: str) -> str:
    e = html.escape

    def link(url: str, text: str) -> str:
        return f'<a href="{e(url)}">{e(text)}</a>' if url.startswith("https://") else e(text)

    rows = "\n".join(f"""      <tr>
        <td>{link(p['url'], p['name'])}<div class="d">{e(p['description'])}</div></td>
        <td><span class="stage {e(p['stage'])}">{e(p['stage'])}</span></td>
        <td>{link(p['play'], '▶ play') if p['play'] else '—'}</td>
        <td>{link(p['ci_url'], p['ci'])}</td>
        <td>{e(p['pushed'])}</td>
      </tr>""" for p in projects) or '      <tr><td colspan="5">No projects yet.</td></tr>'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>factory status</title>
<style>
  :root {{ --bg:#fff; --fg:#1f2328; --muted:#59636e; --line:#d1d9e0; --ok:#1a7f37; --bad:#cf222e; }}
  @media (prefers-color-scheme: dark) {{ :root {{ --bg:#0d1117; --fg:#e6edf3; --muted:#9198a1; --line:#3d444d; --ok:#3fb950; --bad:#f85149; }} }}
  body {{ background:var(--bg); color:var(--fg); font:15px/1.5 system-ui,sans-serif; margin:0 auto; max-width:900px; padding:16px; }}
  table {{ border-collapse:collapse; width:100%; }}
  th, td {{ border-bottom:1px solid var(--line); padding:8px 6px; text-align:left; vertical-align:top; }}
  th {{ color:var(--muted); font-weight:600; font-size:13px; }}
  .d, footer {{ color:var(--muted); font-size:13px; }}
  .stage {{ border:1px solid var(--line); border-radius:10px; padding:0 8px; font-size:13px; }}
  .wrap {{ overflow-x:auto; }}
  a {{ color:inherit; }}
</style>
</head>
<body>
  <h1>factory status</h1>
  <p class="d">Projects in <strong>{e(owner)}</strong>, built from ideas by
  <a href="https://github.com/krmayankk/factory">factory</a>.</p>
  <div class="wrap"><table>
    <thead><tr><th>Project</th><th>Stage</th><th>Play</th><th>CI on main</th><th>Last push</th></tr></thead>
    <tbody>
{rows}
    </tbody>
  </table></div>
  <footer><p>Updated {e(generated)} UTC · hourly and after every new project.</p></footer>
</body>
</html>
"""


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--owner", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    projects = collect(a.owner)
    (out / "index.html").write_text(render(a.owner, projects, now), encoding="utf-8")
    print(f"{len(projects)} project(s) → {out / 'index.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
