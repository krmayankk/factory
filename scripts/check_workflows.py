#!/usr/bin/env python3
"""Workflow policy: the supply-chain and trigger rules from PLAN.md's threat model.

For every workflow file under the given directories:
  - every `uses:` of a remote action is pinned to a full 40-hex commit SHA
    (local `./` actions and `docker://...@sha256:` images are allowed);
  - `pull_request_target` is never used (it runs with secrets on fork PRs);
  - a top-level `permissions:` block is declared (no inheriting the token's defaults).

Stdlib only; line-based on purpose — the rules are about literal text a reviewer reads.
Usage: check_workflows.py DIR...
"""
from __future__ import annotations

import pathlib
import re
import sys

USES = re.compile(r"^\s*(?:-\s*)?uses:\s*['\"]?([^'\"\s#]+)")
PINNED = re.compile(r"@[0-9a-f]{40}$")
DOCKER_PINNED = re.compile(r"^docker://.+@sha256:[0-9a-f]{64}$")
# The trigger, not the words: as a key (`pull_request_target:`), a list item, or inside
# an `on:` line. A step *named* "no pull_request_target" is not a trigger.
TARGET_TRIGGER = re.compile(
    r"^\s*(?:-\s*)?pull_request_target\s*:?\s*(?:#.*)?$"
    r"|^on:.*\bpull_request_target\b",
    re.MULTILINE)


def check_file(path: pathlib.Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    if TARGET_TRIGGER.search(text):
        errors.append("uses pull_request_target (banned: secrets on fork PRs)")
    if not re.search(r"^permissions:", text, re.MULTILINE):
        errors.append("no top-level `permissions:` block")
    for n, line in enumerate(text.splitlines(), 1):
        m = USES.match(line)
        if not m:
            continue
        ref = m.group(1)
        if ref.startswith("./"):
            continue
        if ref.startswith("docker://"):
            if not DOCKER_PINNED.match(ref):
                errors.append(f"line {n}: docker image not pinned by digest: {ref}")
        elif not PINNED.search(ref):
            errors.append(f"line {n}: action not pinned to a commit SHA: {ref}")
    return [f"{path}: {e}" for e in errors]


def main(dirs: list[str]) -> int:
    files = sorted(p for d in dirs for p in pathlib.Path(d).glob("*.y*ml"))
    errors = [e for f in files for e in check_file(f)]
    for e in errors:
        print(e)
    print(f"{len(files)} workflow file(s), {len(errors)} policy error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or [".github/workflows"]))
