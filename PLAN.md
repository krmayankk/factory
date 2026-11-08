# factory — plan

**Idea to running system, from a phone, without an always-on machine — and without a
path by which an idea, an agent or a leaked token can spend money or touch cloud
resources unapproved.**

Part 1 is the system end to end. Part 2 is the security model, the budget model and the
build order, in enough detail to review. Anything not built yet is marked **deferred**
with the reason; nothing here is aspirational without saying so.

---

# Part 1 — the system

## Where this sits

factory is the first component of an agent-native development platform (see sentinel's
PLAN.md, "Where sentinel sits in the fleet"). Projects such as `gpu-inference` and
`revbench` are *built by* the platform; factory is how new ones start and how every one
of them gets the same guardrails. sentinel is the judgment gate inside it.

## The loop

```
 1 CAPTURE   Claude Code cloud session on this repo, from the Claude app (typed or dictated).
             Back-and-forth until the idea is sharp.                         $0
 2 PROPOSE   The session writes ideas/<name>.md (problem, plan, needs, cost estimate)
             and opens a PR. CI validates the file. sentinel reviews it.     $0
 3 APPROVE   You merge the PR (phone).  ← human gate #1: a project may exist
 4 CREATE    A workflow creates repo <name> from template/: gates, branch protection,
             a least-privilege cloud role, budget tags. Reports back on the PR.  $0
 5 BUILD     Cloud sessions open PRs in <name>. CI on GitHub-hosted runners runs
             lint, tests and a kind cluster with mocks. sentinel reviews.    $0
 6 SPEND     Anything that costs money runs in a `live` workflow that waits for you.
             ← human gate #2: money may be spent. Then: short-lived credentials,
             hard budget, automatic teardown, evidence posted to the PR.
```

**Nothing of yours is always on.** Capture and building run in Anthropic's cloud
sessions; CI and provisioning on GitHub-hosted runners; spend in AWS. Your devices only
send messages and approve.

## How to use it

**One-time setup** (from a laptop; each step is yours because it acts on your accounts)

| Step | Command / place | Why |
|---|---|---|
| Publish this repo | `cd ~/src/factory && gh repo create krmayankk/factory --public --source . --remote origin --push && git push -u origin plan/f0` | the factory has to exist on GitHub before a cloud session can open it |
| Claude's GitHub access | GitHub → Settings → Applications → Claude → **Only select repositories** (add `factory`) | least privilege; F1 adds each new project automatically |
| Your approvals are 2-factor | GitHub → Settings → Password and authentication → passkey or 2FA on | the two human gates are only as strong as your GitHub login |
| No surprise Claude bill | claude.ai → Settings → Usage → paid extra usage **off** | plan limits become the hard stop |

**Every day** — from the Claude mobile app or Claude desktop, **Code tab, cloud session**
(not a local one: cloud sessions keep working with every device closed):

| You want to | Do this | Where |
|---|---|---|
| Capture an idea | new session on `factory`; talk it through; "write it up as `ideas/<name>.md` and open a PR" | Claude app / desktop |
| Refine an idea | comment on its PR, or keep talking in the same session | GitHub app / Claude app |
| Start the project | merge the idea PR (gate #1) | GitHub app |
| Build | new session on the project repo: "build per `ideas/<name>.md`, small PRs" | Claude app / desktop |
| Spend money | approve the waiting `live` run (gate #2) | GitHub app |
| Improve the factory itself | session on `factory`; describe the change; merge its PR | Claude app / desktop |

**Voice:** use the phone or computer keyboard's own dictation (the mic key) in the
session's prompt box — it works everywhere. Claude Code's built-in `/voice` dictation is
terminal-only and does not work in cloud sessions; the Claude app's voice-chat mode
cannot see repositories. Replies are text.

Until F1 ships, creating the project repo after the merge is manual (github.com/new,
then add it to Claude's repository access).

**Where a project's result lives** — the proposal picks the cheapest row that works:

| The project needs | It runs on | Cost |
|---|---|---|
| A page or browser app (games, tools, dashboards) | GitHub Pages, or a Claude artifact (can also store data and call Claude) | free |
| A small backend (API, light database) | a serverless free tier (Cloudflare, AWS Lambda) | free–cents |
| A container, VM or GPU | AWS, behind gate #2 and the budget stop | per hour, auto-teardown |

GitHub Actions *tests* everything (including throwaway kind clusters); it never hosts —
jobs end within 6 hours and accept no inbound connections.

## Invariants (enforced, not intended)

1. **No long-lived cloud credentials exist outside your own machine.** CI reaches AWS
   only through GitHub OIDC; agent sessions hold no cloud credentials at all.
2. **Channels propose; they never execute.** Every input — chat, voice, idea text — ends
   as a file in a PR. Nothing a message says runs until a gate passes.
3. **Two human gates:** a project exists only after a merge you make; money is spent
   only after an approval you give. Everything between runs unattended.
4. **$0 first.** Every change passes the free tier (hosted runners, kind, mocks) before
   it may request paid compute.
5. **Every budget has a hard stop that does not depend on the agent behaving:** AWS
   (budget action revokes spend permissions), LLM provider (prepaid cap), Claude (plan
   limits, no paid overage), GitHub Actions (public repos; spending limit $0).
6. **Teardown is proven, not assumed.** Every live run ends in teardown that verifies
   zero tagged resources remain; an independent reaper sweeps on a schedule.
7. **Evidence or it didn't happen.** Every live run and every UI change leaves artifacts
   on its PR: logs, screenshots, video, cost.

## Build order

| Phase | Delivers | Spend |
|---|---|---|
| **F0** | This plan, reviewed | $0 |
| **F1** | Ideas as PRs (schema + validation), repo template, repo creation via a GitHub App, branch protection as code | $0 |
| **F2** | AWS guardrail baseline: OIDC provider, budget + budget action, role factory with a permissions boundary, reaper | ~$0 (IAM and OIDC are free; the first two action-enabled budgets are free) |
| **F3** | First project onboarded: `gpu-inference` live runs via `live` workflows | per approved run |
| **F4** | Evidence pipeline: Playwright screenshots/video on PRs, per-PR previews for web projects | $0 |
| **F5** | Laptop as an optional self-hosted runner tier, private repos only | $0 |

**Deferred, deliberately:**
- *WhatsApp / iPhone-Shortcut capture* — the Claude app already covers capture with no
  extra credential; a second channel adds attack surface for convenience only. Revisit
  after F3.
- *OpenClaw as an always-on runtime* — requires an always-on host, contrary to the goal;
  revisit when proactive agents are needed (sentinel PLAN, runtime framing).
- *Merge without a human* — requires sentinel's autonomous merge gate (sentinel v0.7.5)
  with a measured operating point. Until then gate #1 stays human.
- *Separate sandbox AWS account under Organizations* — stronger isolation via SCPs;
  deferred until credits/billing across accounts is confirmed. F2 gets most of the
  benefit inside one account.
- *Pay-per-second serverless GPU tier* — added when a project needs GPU checks smaller
  than a cluster.

---

# Part 2 — details

## Threat model

| Threat | Control |
|---|---|
| Leaked GitHub token or session | No cloud keys to steal (OIDC only). The repo-creation credential is a GitHub App key held only in a protected environment of this repo, usable only by a workflow on `main`. |
| Malicious / injected idea text ("ignore previous instructions, run …") | Idea text is data in a file. Validation is schema-based; creation uses only validated fields (name, visibility, cloud: yes/no). Agent sessions have no cloud credentials. |
| Agent writes dangerous code | Every change is a PR through CI + sentinel; branch protection blocks direct pushes to `main`; live runs need your approval and run under a role that cannot exceed its boundary. |
| Fork PR on a public repo tries to reach secrets or cloud | Fork PRs run with a read-only token and no secrets. Live workflows trigger only on `workflow_dispatch` / `push` to `main` and require the `live` environment. `pull_request_target` is banned by lint. |
| Compromised third-party Action | Actions pinned by full commit SHA; Dependabot updates them as reviewed PRs; default `permissions: contents: read` per workflow. |
| Role escalation in AWS | Project roles can only be created by the factory role, only under the `factory-` name prefix, and only with the factory permissions boundary attached (IAM condition `iam:PermissionsBoundary`). The boundary denies IAM changes, other regions and non-allowlisted instance types. |
| Role abuse within its rights | OIDC trust is pinned to one repo + the `live` environment + `main`. Resources are tag-scoped to the project. Budget action revokes spend at the cap. |
| Runaway or forgotten resources | Teardown in an `always()` step; TTL on GPU capacity (scale to zero); hourly reaper deletes anything older than its TTL; orphan sweep proves zero. |
| Self-hosted runner executes untrusted code | F5 runners serve **private repos only** and only `push` / `workflow_dispatch` events — never PRs. |

## Budgets and hard stops

| Budget | Hard stop | Notes |
|---|---|---|
| AWS | AWS Budgets **budget action**: at the monthly cap, attach a deny policy to all `factory-*` roles. Alerts at 50/80% to email. | Independent of the agent; works even if every workflow is broken. |
| LLM provider (sentinel) | Prepaid credit with no auto-recharge, or a per-key credit limit | Reviews stop, they don't bill. |
| Claude | Plan usage limits; paid extra usage **off** | Cloud sessions and the GitHub Action draw from the plan. |
| GitHub Actions | Public repos: standard hosted runners are free. Account spending limit $0 so private-repo overage fails instead of billing. | Larger and GPU runners are always paid — not used. |

## The cost ladder

| Tier | Where | Cost | For |
|---|---|---|---|
| 0 | GitHub-hosted runners: kind cluster, mocks, unit and contract tests | $0 (public) | every PR, always |
| 0.5 | Laptop self-hosted runner (F5) — jobs queue while it is off | $0 | heavier private tests |
| 1 | Hosted model APIs | cents | projects that *use* a model |
| 2 | AWS spot capacity | ~60–70% below on-demand | live tests that tolerate interruption |
| 3 | AWS on-demand | list price | live runs needing guaranteed capacity |

A change may request tier N only after passing tier N−1 on the same commit.

## What every new repository starts with (`template/`)

- CI: lint, unit tests, a kind-cluster job with mocks (tier 0), Actions pinned by SHA,
  least-privilege `permissions`.
- sentinel review workflow and a `CLAUDE.md` with the project's invariants.
- Branch protection on `main` as code: PR required, checks required, no force pushes.
- `live` environment: required reviewer (you), deployment branch `main` only.
- An AWS role `factory-<name>` with the boundary, created by the factory (F2) — only if
  the idea declares `cloud: aws`.
- `Makefile` contract: `up`, `down`, `verify`, `evidence` — the same shape as
  `gpu-inference`.
- Cost tags (`Project=<name>`, `Ephemeral=true`) wired as provider defaults.

## The idea file (`ideas/<name>.md`)

Front matter is the only machine-read part; the body is for you.

```yaml
---
name: spot-price-tracker        # becomes the repo name; [a-z0-9-], unique
visibility: public              # public | private
cloud: none                     # none | aws
monthly_cap_usd: 5              # must be <= the account-wide cap
---
```

CI rejects an idea PR whose front matter fails the schema or whose repo name exists.

## GitHub Actions: what is free (checked 2026-10-31)

- **Public repositories:** standard GitHub-hosted runners are free.
- **Private repositories:** a monthly free-minute quota (2,000 on the Free plan per
  third-party guides — confirm on GitHub's billing page), then per-minute; hosted runner
  prices were cut up to 39% on 2026-01-01.
- **Self-hosted runners:** no GitHub fee today; a proposed $0.002/min charge for
  private repos was postponed with no new date.
- **Larger and GPU runners:** always paid; factory does not use them.

## Decisions this plan asks you to make

1. GitHub App vs fine-grained token for repo creation — **recommend the App**
   (short-lived installation tokens, explicit permissions, revocable in one place).
2. The account-wide AWS monthly cap (suggest $30 while credits last).
3. Default visibility for new projects (suggest public: free CI, and it is a showcase;
   private when the idea says so).
