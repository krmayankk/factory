---
name: bookmark-digest      # becomes the repo name: 3-40 chars, [a-z0-9-]
visibility: public         # public (private needs the org on Team — see PLAN.md)
cloud: none                # none | aws
monthly_cap_usd: 0         # 0 when cloud: none; never above the account cap
---

## Problem
I bookmark far more on X than I ever read. The pile includes threads, articles, and
long YouTube podcasts and interviews that I saved meaning to "watch later", and it
grows every day. Meanwhile I miss what's new in tech and science unless it happens to
cross my feed. I don't need more to read. I need someone to go through the pile, tell me
in a few lines what each item actually said and whether it's worth my full attention,
and hand it to me in a form I can take in while driving, walking or between meetings:
an email, an audio episode in my podcast app, and a page I can search later.

## Smallest useful version
A pipeline with three stages. Each stage hands over files, not commands, so that text
taken from the web can never run anything.

**1. Collect (GitHub Actions, scheduled, no AI).**
- **X bookmarks:** read through the X API's bookmarks endpoint
  (`GET /2/users/:id/bookmarks`, OAuth 2.0 user context, scopes `bookmark.read
  tweet.read users.read offline.access`). The first run pulls the whole backlog. Later
  runs pull new bookmarks every 6 hours. Already-seen IDs are skipped, so nothing is
  paid for twice.
- **Expand each bookmark into what it points at:**
  - the tweet or thread text;
  - for a linked article, the readable text (fetched once, polite User-Agent, robots
    respected);
  - for a YouTube link, the video's title, channel and length, plus its transcript.
- **Discovery feeds ("What's new in the world"):** a small fixed list in `sources.yml`,
  changed by PR. All of them are key-less:
  - Hacker News top stories (Algolia API, score ≥ 300);
  - arXiv new submissions in `cs.AI`/`cs.LG` (RSS; only the top few by a simple rule);
  - YouTube channel RSS (`/feeds/videos.xml?channel_id=…`) for a list of podcast and
    interview channels I pick.
- **Output:** one JSON file per item in a `queue/` folder, with source, URL, title,
  length, text or transcript, and fetched-at. Items are capped in size, and anything over
  the cap is truncated with a note.

**2. Summarize (a scheduled Claude session, once a day, on my Claude subscription).**
- The session reads the next batch from `queue/`. Newest bookmarks go first, then a
  daily slice of the backlog (default 40 items a day, configurable) until the backlog
  is gone.
- **Per item it writes:**
  - a one-line "what this is";
  - 3–6 key points, plus the notable claim, number or quote with a timestamp for
    videos;
  - a verdict: *skip*, *skim* or *worth the full thing*, with one sentence why;
  - topic tags.
- **Per digest it writes:**
  - a short "Top 3 today";
  - a "What's new in the world" section from the discovery items.
- **Output:** one `digests/YYYY-MM-DD.json` file, pushed to a `digests` data branch
  (never to `main`). The session has no secrets and never emails, posts or fetches
  anything itself. Everything it reads is treated as untrusted data, and its only output
  is that JSON file.

**3. Publish (GitHub Actions, on a push to `digests`, no AI).**
- **Validate:** check the digest against a JSON schema (lengths, allowed fields, links
  must be the item's own URL). A digest that fails is not published, and a "digest
  rejected" issue is opened instead.
- **Web page (GitHub Pages):** the newest digest first, an archive by date, search by
  text and tag, and a filter by verdict. Each item links to the original.
- **Audio, a podcast feed:**
  - the digest is turned into a narration script (Top 3, then each *worth it* and *skim*
    item, then "What's new");
  - it is spoken by **Piper**, open-source text-to-speech running on the runner's CPU,
    and encoded to MP3 with ffmpeg;
  - it is published as an episode in `feed.xml`, a standard podcast RSS feed I subscribe
    to by URL in my podcast app;
  - target length is 10–15 minutes, with chapters per item where the app supports them.
- **Email:** each digest is opened as a GitHub issue titled "Digest — 28 Nov: 3 worth
  it, 12 skim", with a body of Top 3, verdicts and links. GitHub emails it to me and
  pushes it to my phone. No mail credentials exist anywhere, so no injected text can
  send mail to someone else. Closing the issue marks the digest as read.

**Privacy (the repo is public).**
- The page, the feed and the issues show summaries of public posts and videos, and my
  choice of them. That is visible to anyone who finds the repo.
- No DMs, no private posts and no account data are fetched. The X token lives only in
  repo secrets.
- If that's too public, the fix is the org on Team (private repo with guardrails), not
  an unguarded private repo.

**X token handling.** X's OAuth 2.0 refresh tokens are long-lived but rotate on use.
- The workflow keeps the current token encrypted (with a key held only in repo
  secrets) in an Actions cache, and refreshes it each run.
- A failed refresh opens a "reconnect X" issue with a one-command re-authorize script
  to run locally.
- The source probe (below) confirms whether rotation works this way before any feature
  relies on it.

Not in v1: summarizing bookmarks from other apps (Pocket, Safari, YouTube "Watch
later"), replying or un-bookmarking on X, personal voice cloning, translation, chat
with my archive, and any paid text-to-speech or hosting.

## How we'll know it works
- **First PR, source probe (a gate):** a workflow on a GitHub-hosted runner fetches each
  source once and records status, a sample and timing as evidence:
  - the X bookmarks endpoint, with a real token and 5 bookmarks, plus the credit
    actually charged for them, read from the X Developer Console;
  - one token refresh, run twice in a row;
  - one article;
  - one YouTube transcript (YouTube often blocks transcript requests from cloud IPs;
    if it does, the fallback is metadata plus the video description, labelled "no
    transcript", and the kill criteria apply if most videos fall back);
  - HN, arXiv and one channel RSS.

  A source that fails is dropped or replaced before any feature uses it.
- **CI, offline and $0:**
  - each parser is tested against recorded fixtures;
  - already-seen bookmarks are not fetched again;
  - a digest that violates the schema is rejected, including a digest containing an
    injected instruction or a link that isn't the item's URL;
  - Piper turns a fixture digest into an MP3 of the expected length;
  - `feed.xml` validates as podcast RSS (enclosure, duration, GUIDs stable across
    rebuilds).
- **Live, after merge:**
  - **Day 1:** the backlog count matches the number of bookmarks shown on X, give or
    take 1%.
  - **Each day:** a digest issue arrives by email, and the episode plays in a real
    podcast app subscribed by URL (Apple Podcasts or Pocket Casts) on my phone.
  - **Pages:** the URL loads at phone width with no console errors, and searching a tag
    finds an item from a past digest.
  - **Backlog progress:** shown on the page ("1,240 left, about 31 days at 40/day")
    and going down.
- **Quality check, a human gate:** for the first week, I mark each item in the digest
  issue as "summary right" or "summary wrong". The build continues past v1 only if at
  least 9 in 10 are right.

## Cost
- **GitHub Pages and Actions** (public repo, standard runners): $0. That covers
  collection, validation, Piper text-to-speech, MP3 hosting and the feed.
- **Summarizing:** a scheduled Claude session on my existing Claude subscription. No API
  key and no new bill, but it uses my plan's usage, about one session a day.
- **X API:** pay-per-use with prepaid credits and auto-recharge off, so the balance is a
  hard cap that can't be exceeded.
  - Third-party trackers list bookmark reads at about $0.001 each (unverified; check in
    the X Developer Console before topping up).
  - At that rate a backlog of ~2,000 costs ~$2, and ~20 new bookmarks a day cost ~$0.60
    a month.
  - One $5 top-up should last months. The front matter's `monthly_cap_usd` covers AWS
    only, so this spend is controlled by the prepaid balance instead.
- **All other sources:** free and key-less, throttled to fair use.
- **Worst-case monthly spend:** $0 of new cloud, plus whatever is left of a $5 X credit
  balance.

## Kill criteria
- **X access:** if the probe shows bookmarks can't be read with pay-per-use credits, or
  the token can't be refreshed unattended, fall back to share-to-capture: send a link
  to a GitHub issue from the phone's share sheet. Archive if that is too clunky to use
  for two weeks.
- **YouTube transcripts:** if more than half of YouTube bookmarks get "no transcript"
  from GitHub runners and there is no free fix, drop video summaries. Archive if the
  digest isn't worth it without them, since videos are half the point.
- **Accuracy:** if, after one prompt-tuning PR, fewer than 9 in 10 summaries are right,
  stop and archive. A wrong summary is worse than none.
- **Usage:** if, a month after v1, I'm not listening to the episodes or opening the
  digests, archive it.
- **Reliability:** if the scheduled Claude session misses more than 2 days a week for
  two weeks, move summarizing to the Claude API (a new idea PR with an `aws`-style
  spending cap) or archive.
