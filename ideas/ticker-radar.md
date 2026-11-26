---
name: ticker-radar         # becomes the repo name: 3-40 chars, [a-z0-9-]
visibility: public         # public (private needs the org on Team — see PLAN.md)
cloud: none                # none | aws
monthly_cap_usd: 0         # 0 when cloud: none; never above the account cap
---

## Problem
I want one glanceable page for the parts of the market I actually follow: the stocks on
my watchlist, T-bill yields, the IPOs I'm waiting for, and the handful of economic
numbers that move everything (CPI, jobs, the Fed). I also want the dates that matter
coming up: FOMC meetings, CPI and jobs releases, T-bill auctions, IPO pricing and
lock-up expiries. Today that means a brokerage app, a finance site full of ads, the
Treasury site and a calendar I keep by hand, and dates get missed. I want it free, from
a link on my phone, with alerts arriving where I already look (GitHub notifications),
and with no account, server or paid data feed.

## Smallest useful version
A static page on GitHub Pages, kept fresh by scheduled GitHub Actions workflows.
There's no server and no cloud.

**You add and remove things on the page itself.** You never edit a file on GitHub.
- **The watchlist lives on your device,** in the browser's storage. It's private (it
  never reaches the public repo), it works with no account, and it changes instantly.
- **The workflows publish data for a whole universe, not for your list.** That
  universe covers every US-listed stock and ETF, the IPO pipeline and a catalog of
  indicators. Each item gets one small JSON file (`data/t/NVDA.json`), and the page
  loads only the files for what you're watching. That's why any ticker can be added
  at any moment without a rebuild.
- **The data is deployed with the site,** not committed back to the repo, so the repo
  doesn't grow every day.

**1. Watchlist stocks.** Each card shows the last close, daily change in %, 52-week
range and a 30-day sparkline. Prices are end-of-day or delayed, and the page says
they aren't real-time and aren't advice.
- **Adding:** a search box ("NVDA" or "nvidia") autocompletes against every US-listed
  ticker, and picking a result adds its card immediately.
- **Managing:** swipe or ✕ removes a card, drag reorders the cards, and each card has
  its own alert threshold.

**2. T-bills and rates.** Today's yields for the 4-, 8-, 13-, 17-, 26- and 52-week
bills, with the 2- and 10-year notes for context. It shows the change over a week and
over a month, and the next bill auctions with their dates and the results of recent ones.

**3. IPO radar.** Upcoming and recent US IPOs. Tap ☆ on any IPO to watch it; watched
names are pinned to the top, and searching by company name finds filings not yet in
the list.
Each IPO gets a timeline of its key dates:
- registration filed (S-1/F-1);
- price range set (S-1/A with a range);
- priced (424B4);
- first trade;
- quiet-period end (listing + 25 days);
- lock-up expiry (listing + 180 days, or the date in the prospectus when it can be
  parsed).

Computed dates are labelled *estimated*.

**4. Economic indicators.** Latest value, previous value, change and a small chart.
You choose which ones to show from a catalog of about 30 series. These are on by
default:
- CPI and core CPI (year over year);
- unemployment rate;
- nonfarm payrolls;
- initial jobless claims;
- effective fed funds rate;
- 10y–2y spread;
- real GDP growth;
- PCE inflation;
- 30-year mortgage rate.

**5. Key dates calendar.** One merged "what's coming" list for the next 30 days, linked
from each section:
- FOMC meetings, and the day minutes are released;
- CPI, jobs report, GDP and PCE releases;
- T-bill auctions;
- IPO pricing, listing and lock-up dates.

It's also published as an `.ics` file you can subscribe to from a phone calendar.

**6. Alerts.**
- **Personal alerts, on the page:** when you open the page, a "since your last visit"
  strip lists what changed for things you watch:
  - a ticker moved more than its threshold (default ±5%);
  - a watched IPO set a range, priced, listed, or is within 7 days of lock-up expiry.

  The server never sees your watchlist, so it can't send personal alerts. That's the
  price of keeping it private.
- **Market-wide alerts, as GitHub issues** (one per event, deduplicated, closing one
  acknowledges it):
  - the 13-week bill yield moves more than 15 bp in a week;
  - a source has been down for 3 runs in a row;
  - a "week ahead" issue every Monday with that week's key dates.

  GitHub's phone and email notifications deliver these.

**Data sources.** Every value on the page carries its source and an as-of time. No
source needs an API key.

| Data | Source | Kind | Notes |
|---|---|---|---|
| Bill and note yields | US Treasury daily par yield curve and bill rates (home.treasury.gov CSV/XML) | official | published each business day, mid-afternoon ET |
| Bill auctions (upcoming and results) | TreasuryDirect `TA_WS` JSON (`/securities/announced`, `/securities/auctioned`) | official | |
| IPO filings and dates | SEC EDGAR (full-text search and submissions JSON), filing types S-1, S-1/A, F-1, 424B4 | official | needs a descriptive User-Agent; stay under 10 requests per second |
| Ticker search (the universe) | SEC `company_tickers.json` and `company_tickers_exchange.json` | official | refreshed daily; feeds the autocomplete |
| Economic indicators | FRED key-less CSV download (`fredgraph.csv?id=SERIES`); catalog of about 30 series, including CPIAUCSL, CPILFESL, UNRATE, PAYEMS, ICSA, EFFR, T10Y2Y, A191RL1Q225SBEA, PCEPI, MORTGAGE30US | official (St. Louis Fed) | |
| Release dates | BLS release-schedule `.ics`; Fed FOMC calendar page, plus a yearly `dates/fomc-YYYY.yml` checked in by PR as a fallback | official | |
| Stock prices (whole US universe) | Stooq daily bulk file for US listings; if that's unavailable, per-ticker daily CSV for a smaller universe (below) | **unofficial** | no SLA; second key-less source as a cross-check is TBD |
| IPO expected listing dates | Nasdaq IPO calendar JSON | **unofficial** | may block bots; EDGAR filings remain the ground truth |

**How data stays honest (reliability).**
- **Freshness:** each card shows when its data was last updated. When data is
  older than expected, the card is greyed and marked "stale", and the page never shows
  old numbers as current. "Expected" is 1 business day for prices and yields, and the
  next scheduled release for indicators.
- **Errors keep the last good data:** a source that errors or returns something
  malformed never overwrites good data, and the page shows "source down since …".
- **Health check:** each source has a health record. If a source fails 3 runs in a
  row, the workflow opens one "source down" issue, and closes it when the source
  recovers.
- **Cross-checks:**
  - Stock closes are compared with a second source when one is configured, and
    disagreements over 1% are flagged.
  - IPO dates from Nasdaq are shown only alongside a matching EDGAR filing.
- **Labels:** official and unofficial sources are labelled on the page.

**The universe, and what happens for a ticker outside it.**
- **Full universe:** every US-listed stock and ETF in SEC's ticker list, priced from the
  bulk daily file. This is about 10k tickers, and with one small file per ticker the
  site stays well under the 1 GB Pages limit.
- **Fallback:** if the bulk file isn't available, the universe shrinks to the S&P 500,
  the Nasdaq-100, US IPOs from the last 12 months and the 100 most-searched tickers,
  priced one CSV at a time within the source's fair-use limits.
- **Outside the universe:** a ticker that isn't priced yet still shows up in search,
  marked "no price data". It never shows a wrong or empty number.
- **Privacy:** nothing about your watchlist leaves your device. The "most-searched"
  list above is not built from your searches; it's a fixed list in the repo, changed by PR.
- **Moving devices:** an export/import button saves the watchlist as a short code or
  link, so you can carry it to another phone. There's no sync and no account.

**Schedule.**
- Prices for the whole universe: after the US close on trading days.
- Yields and auctions: once per business day after Treasury publishes.
- EDGAR: twice a day.
- Indicators and calendars: daily.

All of this stays well inside free Actions minutes on a public repo.

Not in v1: real-time or intraday quotes, portfolio or P&L tracking, brokerage logins,
accounts or watchlist sync across devices, personal push notifications, non-US markets,
arbitrary FRED series outside the catalog, and any paid or API-key data source.

## How we'll know it works
- **First PR, source probe (a gate):** a workflow on a GitHub-hosted runner fetches each
  source above once and records the HTTP status, a sample and the response time as
  evidence. A source that fails here is dropped or replaced before any feature uses it.
  If prices or EDGAR can't be reached without a key, the kill criteria apply.
- **CI, offline and $0:** fetchers and parsers are tested against recorded fixtures
  for every source:
  - parsed values match the expected ones;
  - the IPO timeline computes the right estimated quiet-period and lock-up dates;
  - a +6% move or a 20 bp bill move produces exactly one alert issue in a dry run,
    and running it again produces none;
  - a malformed or failed source keeps the last good data and marks it stale;
  - the universe build publishes one JSON file per ticker and a search index; a ticker
    missing from the price source is marked "no price data", never zero.
- **Live, after merge:** the scheduled runs show:
  - at least 95% of the universe with a close from the last trading day (the run log
    reports the exact count and lists the misses);
  - the 13-week bill yield from the last business day;
  - each listed indicator's latest release;
  - at least one FOMC date and one CPI release date in the next 90 days in the calendar.
- **Browser:** the Pages URL loads on desktop and a phone-sized viewport with no
  console errors. The `.ics` file parses and imports into a calendar app. A Playwright
  test covers:
  - every section renders with values, sources and as-of times;
  - typing "nvidia" in search and picking NVDA adds a card with a price;
  - the card is still there after a reload, and is gone after ✕;
  - no request carries the watchlist off the device (the test checks every network
    request the page makes).
- **Alerts:**
  - In the browser test, a fixture with a +6% move shows up in "since your last visit".
  - In production, a "week ahead" issue appears on Monday.

  The PR includes screenshots of the page, the search and the issue.

## Cost
GitHub Pages and GitHub Actions on a public repo: $0. Every data source is free and
needs no API key: US Treasury, TreasuryDirect, SEC EDGAR, FRED CSV, BLS, the Fed, Stooq
and Nasdaq. Requests are throttled to each source's fair-use limits, and SEC gets a
descriptive User-Agent. The only credential is the workflow's own `GITHUB_TOKEN`, used
to deploy Pages and open market-wide issues. The watchlist lives on your device. There's
no cloud, no backend and no paid feed.
Worst-case monthly spend: $0.

## Kill criteria
- If, after the source probe, there's no reliable key-less source for daily stock prices
  or for EDGAR from GitHub runners, and the only fix is a paid or key-gated API, then
  stop and archive. If the bulk file is out but per-ticker prices work, continue with the
  fallback universe rather than stop.
- If a single unofficial source (Stooq or Nasdaq) breaks for more than 2 weeks and has no
  key-less replacement, then drop that section rather than add a paid feed. If the page
  is no longer useful without it, archive.
- If, a month after v1, I'm not opening the page or acting on alerts, archive it.
- If alerts are noisy (more than about 3 a week that I ignore) after one tuning PR,
  stop adding sources and features and rethink the thresholds or archive.
