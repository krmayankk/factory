---
name: ticker-radar         # becomes the repo name: 3-40 chars, [a-z0-9-]
visibility: public         # public (private needs the org on Team — see PLAN.md)
cloud: none                # none | aws
monthly_cap_usd: 0         # 0 when cloud: none; never above the account cap
---

## Problem
I want one glanceable place for the handful of stocks I care about and the IPOs I'm
waiting for: today's price and move, a small trend, and a nudge when something
happens (a big move, an IPO gets a price range or a listing date). Today that means
checking several apps and finance sites full of ads, sign-ups and noise, and IPO dates
are easy to miss. I want it free, from a link on my phone, with alerts arriving where I
already look (GitHub notifications), and with no account, server or paid data feed.

## Smallest useful version
A static page on GitHub Pages, kept fresh by a scheduled GitHub Actions workflow
(no server, no cloud):
- **Watchlist** in `watchlist.yml`: tickers (e.g. `AAPL`, `NVDA`) and IPO names to
  watch (e.g. a company that has filed but not listed). Because the repo is public, the
  watchlist is public too. That's acceptable for v1, and stated in the README.
- **Prices:** for each ticker, the last close, the daily change in % and a 30-day
  sparkline, from a free source that needs no API key (end-of-day or delayed quotes
  are fine). It isn't real-time and isn't advice, and the page says so.
- **IPO radar:** upcoming IPOs from public SEC EDGAR filings (S-1/F-1, and amendments
  that add a price range), plus expected listing dates where a free calendar has them.
  Watched names are highlighted.
- **Alerts as GitHub issues:** a watched ticker moves more than ±5% in a day (the
  threshold is set per ticker), or a watched IPO files a price range or gets a date.
  One issue per event, with no duplicates; closing it acknowledges it. GitHub's
  phone and email notifications do the delivery.
- **Schedule:** a few runs per trading day plus one IPO scan per day. The data is
  committed as `site/data/*.json`, so history is just git history.
- **The page:** plain HTML and JS with no build step, readable at phone width, and
  showing when the data was last refreshed. It shows a stale-data banner if the last
  successful refresh was more than 2 trading days ago.

Not in v1: real-time quotes, portfolio or P&L tracking, brokerage logins, a private
watchlist, push notifications outside GitHub, and any paid or key-gated data source.

## How we'll know it works
- **CI, offline and $0:** recorded fixtures for every data source are fed to the
  fetchers.
  - Parsed prices, % moves and IPO entries match the expected values.
  - A fixture with a +6% move produces exactly one alert issue in a dry run, and
    running it again produces none.
  - A fixture where a source fails produces a clear error and keeps the last good
    data instead of blanking the page.
- **Live:** after merge, the scheduled workflow's run log shows every watchlist ticker
  with a close dated within the last trading day, and `site/data/prices.json` reflects
  that.
- **Browser:** the Pages URL loads on desktop and a phone-sized viewport with no
  console errors. A Playwright test in CI asserts that every watchlist ticker renders
  with a price, a % change and a sparkline, and that the "last updated" time is shown.
- **Alert:** temporarily lowering one ticker's threshold to 0% opens a real alert
  issue on the next run. The PR includes a screenshot of the issue and of the page.

## Cost
GitHub Pages and GitHub Actions on a public repo: $0. Data comes from free sources
that need no API key: SEC EDGAR (public, needs only a descriptive User-Agent, so
throttle to its fair-access limits) plus a free delayed-quote source. There is no cloud,
no backend and no paid feed, and no secret is needed beyond the workflow's own
`GITHUB_TOKEN`, used to commit data and open issues. Worst-case monthly spend: $0.

## Kill criteria
- If no free, key-less source gives reliable daily prices for the watchlist (it blocks
  CI runners, breaks often or forbids this use in its terms), and the only fix is a paid
  or key-gated API, then stop and archive.
- If, a month after v1, I'm not opening the page or acting on alerts, archive it.
- If alerts are noisy (more than about 3 a week that I ignore) after one tuning PR,
  stop adding sources and features and rethink the thresholds or archive.
