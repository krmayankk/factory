---
name: sky-hoppers          # becomes the repo name: 3-40 chars, [a-z0-9-]
visibility: public         # public (private needs the org on Team — see PLAN.md)
cloud: none                # none | aws
monthly_cap_usd: 0         # 0 when cloud: none; never above the account cap
---

## Problem
Quick, cheerful platform games in the spirit of classic run-and-jump arcade games are
hard to find in a form you can open on a phone in five seconds: most want an app store
install, an account, ads, or a paid download. I want an original, free, browser game —
jump across moving bridges floating in the sky, dodge obstacles, reach the end — that
anyone can play from a link, with nothing to install and nothing to pay.

## Smallest useful version
One static page (HTML5 canvas + plain JavaScript, no build step, no external assets
beyond what is drawn in code) served from GitHub Pages:
- **Original characters**, drawn in code, choosable on the title screen — e.g. *Puff*
  (a small cloud sprite, floaty jump), *Tock* (a wind-up tin robot, fast but heavy) and
  *Mira* (a paper-kite fox, can glide briefly). No borrowed names, art or music.
- **Sky world**: a side-scrolling level of floating bridges — static, sliding
  left/right, bobbing up/down, crumbling after you land, and conveyor bridges.
- **Obstacles**: rolling thunderballs, gusts of wind that push you, spiky storm birds
  on simple patrol paths; falling off the bottom costs a life.
- **Goal**: collect stars along the way, reach the rainbow gate at the end. 3 levels of
  rising difficulty, 3 lives, a best-score kept in `localStorage`.
- **Controls**: arrow keys / A-D + Space on desktop; on-screen left / right / jump
  buttons on phones (touch). Pause on tab blur.
- Simple sound effects generated with WebAudio (mute toggle, off by default on mobile).

Not in v1: online leaderboards, accounts, level editor, any backend.

## How we'll know it works
- The GitHub Pages URL loads on desktop Chrome and on a phone-sized viewport with no
  console errors, and the title screen shows all three characters.
- A Playwright test in CI (GitHub-hosted runner, $0) opens the page, picks a character,
  holds right + jump, and asserts the player's x position increases, a star pickup
  raises the score, and falling off the bottom decrements lives.
- A deterministic "autopilot" test input completes level 1 and reaches the rainbow
  gate (level-complete screen appears) — proves the level is beatable.
- Frame time stays under 16 ms on the CI headless browser (logged by the test).
- Screenshots of title, gameplay and level-complete are attached to each UI PR.

## Cost
GitHub Pages on a public repo: $0. CI on GitHub-hosted runners for a public repo: $0.
No cloud, no backend, no third-party services or paid assets. Worst-case monthly spend:
$0.

## Kill criteria
- After v1 ships, if nobody (including me) plays it more than a couple of times in a
  month, archive it.
- If it cannot hold a smooth 60 fps on a mid-range phone after one focused performance
  PR, stop adding features and reconsider the approach.
- If any feature would need a paid service or backend, it does not go in; if the game
  only seems worth it with one, archive instead.
