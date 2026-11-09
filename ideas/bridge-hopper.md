---
name: bridge-hopper
visibility: public
cloud: none
monthly_cap_usd: 0
---

## Problem
A quick, fun browser game to play on a phone, and the factory's first real project: proof
that an idea can go from a chat to a playable link with no laptop and no cloud spend.

## Smallest useful version
A side-scrolling platformer in the browser. One original character — Pip, a small
lantern-carrying robot — runs right across one level: jump gaps, cross collapsing bridges,
dodge rolling barrels, reach the flag. Touch buttons on phones, arrow keys and space on a
keyboard. Original art drawn in code (no sprites, music or names from existing games).
One level, a timer, and a restart button.

## How we'll know it works
- Playwright in CI loads the page, presses jump and right, and checks Pip's position
  changes and the timer starts — then captures a screenshot on the PR.
- On a phone, the Pages link loads in under three seconds and the level can be finished
  with the touch buttons.

## Cost
$0. Plain HTML, CSS and JavaScript in site/, published by the template's Pages workflow
on a public repository. No backend, no keys, no cloud.

## Kill criteria
If it can't be made playable with touch controls on a phone in a handful of small PRs,
stop, write down what was learned, and archive it.
