#!/usr/bin/env python3
"""Parse and validate idea files (ideas/<name>.md).

Idea files arrive from chat sessions and are untrusted. Only the front matter is
machine-read, and only after every field passes the checks below; nothing from the
body ever reaches a shell. Stdlib only, so the gate has no dependencies to compromise.

Usage:
  idea.py validate FILE...                       exit 1 and list errors if any file fails
  idea.py changed --base SHA --head SHA          print idea files ADDED between two commits
  idea.py check-available --base SHA --head SHA --owner ORG
                                                 fail if an added idea's repo already exists
  idea.py field FILE KEY                         print one validated field
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,38}[a-z0-9]$")
FIELDS = ("name", "visibility", "cloud", "monthly_cap_usd")
# The thinking an idea must show before any agent builds it. Each is a `## ` heading
# with at least a sentence under it.
SECTIONS = ("Problem", "Smallest useful version", "How we'll know it works", "Cost",
            "Kill criteria")
ZERO_SHA = "0" * 40


class IdeaError(Exception):
    pass


def load_config() -> dict:
    return json.loads((ROOT / "config" / "factory.json").read_text())


def parse(path: pathlib.Path) -> tuple[dict, str]:
    """Return (front matter, body). Flat `key: value` lines only; `#` starts a comment."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise IdeaError("must start with a '---' front-matter line")
    try:
        end = next(i for i, l in enumerate(lines[1:], 1) if l.strip() == "---")
    except StopIteration:
        raise IdeaError("front matter is not closed with '---'") from None
    fields: dict[str, str] = {}
    for n, raw in enumerate(lines[1:end], 2):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if raw[:1].isspace():
            raise IdeaError(f"line {n}: nested values are not allowed")
        key, sep, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if not sep or not key:
            raise IdeaError(f"line {n}: expected 'key: value'")
        if key in fields:
            raise IdeaError(f"line {n}: duplicate key '{key}'")
        fields[key] = value
    return fields, "\n".join(lines[end + 1:]).strip()


def validate(path: pathlib.Path, cfg: dict) -> list[str]:
    errors: list[str] = []
    if path.parent.name != "ideas" or path.suffix != ".md":
        return [f"{path}: idea files live at ideas/<name>.md"]
    if path.name.startswith("_"):
        return [f"{path}: files starting with '_' are templates, not ideas"]
    try:
        fields, body = parse(path)
    except (IdeaError, UnicodeDecodeError) as e:
        return [f"{path}: {e}"]

    unknown = sorted(set(fields) - set(FIELDS))
    missing = [f for f in FIELDS if f not in fields]
    if unknown:
        errors.append(f"unknown keys: {', '.join(unknown)}")
    if missing:
        errors.append(f"missing keys: {', '.join(missing)}")

    name = fields.get("name", "")
    if "name" in fields:
        if not NAME_RE.fullmatch(name) or "--" in name:
            errors.append(f"name '{name}': 3-40 chars, [a-z0-9-], starts with a letter, "
                          "no leading/trailing or double '-'")
        elif name in cfg["reserved_names"]:
            errors.append(f"name '{name}' is reserved")
        if path.stem != name:
            errors.append(f"file name must be ideas/{name}.md")

    visibility = fields.get("visibility")
    if visibility is not None:
        if visibility not in ("public", "private"):
            errors.append("visibility must be public or private")
        elif visibility == "private" and not cfg["private_allowed"]:
            errors.append("private projects need the organization on a plan with rulesets "
                          "and environment protection for private repos (PLAN.md, "
                          "visibility rule) — never private without guardrails")

    cloud = fields.get("cloud")
    if cloud is not None and cloud not in ("none", "aws"):
        errors.append("cloud must be none or aws")

    cap_raw = fields.get("monthly_cap_usd")
    if cap_raw is not None:
        if not re.fullmatch(r"\d+", cap_raw):
            errors.append("monthly_cap_usd must be a whole number of dollars")
        else:
            cap = int(cap_raw)
            if cap > cfg["account_monthly_cap_usd"]:
                errors.append(f"monthly_cap_usd {cap} exceeds the account cap "
                              f"{cfg['account_monthly_cap_usd']}")
            if cloud == "none" and cap != 0:
                errors.append("cloud: none means monthly_cap_usd: 0")

    errors.extend(check_sections(body))
    return [f"{path}: {e}" for e in errors]


def sections(body: str) -> dict[str, str]:
    """`## Heading` -> text under it (case-insensitive heading match)."""
    out: dict[str, str] = {}
    current = None
    for line in body.splitlines():
        if line.startswith("## "):
            current = line[3:].strip().lower()
            out[current] = ""
        elif current is not None:
            out[current] += line + "\n"
    return out


def check_sections(body: str) -> list[str]:
    found = sections(body)
    errors = []
    for s in SECTIONS:
        text = found.get(s.lower())
        if text is None:
            errors.append(f"missing section '## {s}'")
        elif len(text.strip()) < 20:
            errors.append(f"section '## {s}' is empty — say something specific")
    return errors


def field(path: pathlib.Path, key: str) -> str:
    errors = validate(path, load_config())
    if errors:
        raise IdeaError("; ".join(errors))
    if key not in FIELDS:
        raise IdeaError(f"unknown field {key}")
    return parse(path)[0][key]


def changed(base: str, head: str) -> list[pathlib.Path]:
    """Idea files ADDED between base and head. Edits and renames never re-provision."""
    if not base or base == ZERO_SHA:
        base = subprocess.run(["git", "hash-object", "-t", "tree", "/dev/null"],
                              check=True, capture_output=True, text=True).stdout.strip()
    out = subprocess.run(
        ["git", "diff", "--no-renames", "--diff-filter=A", "--name-only", base, head,
         "--", "ideas/*.md"],
        check=True, capture_output=True, text=True, cwd=ROOT).stdout
    return [ROOT / p for p in out.split() if not pathlib.Path(p).name.startswith("_")]


def repo_exists(owner: str, name: str) -> bool:
    r = subprocess.run(["gh", "api", f"repos/{owner}/{name}", "--silent"],
                       capture_output=True, text=True)
    if r.returncode == 0:
        return True
    if "Not Found" in r.stderr or "HTTP 404" in r.stderr:
        return False
    raise IdeaError(f"could not check {owner}/{name}: {r.stderr.strip()}")


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate"); v.add_argument("files", nargs="*")
    for c in ("changed", "check-available"):
        s = sub.add_parser(c)
        s.add_argument("--base", required=True); s.add_argument("--head", required=True)
        if c == "check-available":
            s.add_argument("--owner", default="")
    f = sub.add_parser("field"); f.add_argument("file"); f.add_argument("key")
    a = p.parse_args(argv)

    try:
        if a.cmd == "validate":
            cfg = load_config()
            errors = [e for x in a.files for e in validate(pathlib.Path(x).resolve(), cfg)]
            for e in errors:
                print(f"::error::{e}" if "GITHUB_ACTIONS" in os.environ else e)
            print(f"{len(a.files)} idea file(s), {len(errors)} error(s)")
            return 1 if errors else 0
        if a.cmd == "changed":
            for path in changed(a.base, a.head):
                print(path.relative_to(ROOT))
            return 0
        if a.cmd == "check-available":
            if not a.owner:
                print("::warning::PROJECTS_OWNER is not set; skipping the name-collision check")
                return 0
            taken = [p.stem for p in changed(a.base, a.head) if repo_exists(a.owner, p.stem)]
            for name in taken:
                print(f"::error::{a.owner}/{name} already exists — choose another name")
            return 1 if taken else 0
        if a.cmd == "field":
            print(field(pathlib.Path(a.file).resolve(), a.key))
            return 0
    except IdeaError as e:
        print(f"::error::{e}")
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
