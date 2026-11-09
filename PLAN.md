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

**Where projects live.** New projects are created in a dedicated GitHub organization
(`PROJECTS_OWNER`), not the personal account: a GitHub App can create repositories only
in an organization, and the organization is the blast-radius fence — the App's power ends
at it, so personal repositories are unreachable. Existing projects stay where they are;
everything except *creation* (cloud sessions, the `live` gate, OIDC, budgets) applies to a
repository wherever it lives.

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
| Publish this repo | `gh repo create krmayankk/factory --public --source . --push` — **done 2026-11-07** | the factory has to exist on GitHub before a cloud session can open it |
| Projects organization | github.com/account/organizations/new, plan **Free** | the fence new projects live inside (see "Where projects live") |
| Provisioner App | org → Settings → Developer settings → GitHub Apps → New. Webhook off. Repository permissions: Administration, Contents, Workflows, Environments, Pages = read & write; Metadata = read; nothing else. Installable only on this account. Install on the org, **All repositories**. Generate a private key. | the only identity that can create repos; short-lived tokens; one-click revoke |
| Wire the App into factory | environment `provision` (deployment branch `main` only) holding secret `FACTORY_APP_PRIVATE_KEY`; repo variables `FACTORY_APP_CLIENT_ID`, `PROJECTS_OWNER`, `APPROVER` | the key is usable only by a workflow running on `main` |
| Claude's GitHub access | Claude GitHub App: on the org **All repositories**; on the personal account **Only select repositories** (`factory`, plus existing projects you want agents on) | every new project is reachable at once; personal repos stay opt-in |
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
| **F1** | Ideas as PRs (schema + five required sections; `make idea`, `make check-idea`), repo template, all-or-nothing repo creation via a GitHub App, branch protection as code; then a TLA+ model of repo creation checked on every PR | $0 |
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
| Leaked GitHub token or session | No cloud keys to steal (OIDC only). The repo-creation credential is a GitHub App key held only in a protected environment of this repo, usable only by a workflow on `main`; its installation tokens expire in an hour and cannot reach outside the projects organization. |
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
- Branch protection on `main` as code, as two rulesets: `main` binds everyone (PR
  required, `checks` green, no force-push or deletion); `only admin merges` lets only a
  repository admin update `main`, and only by merging a PR — agents propose, never merge.
- `pages.yml`: publishes `site/` to GitHub Pages on every change to `main`, for projects
  that have a `site/index.html`; Pages is switched on at creation.
- `live` environment: required reviewer (you), deployment branch `main` only.
- An AWS role `factory-<name>` with the boundary, created by the factory (F2) — only if
  the idea declares `cloud: aws`.
- `Makefile` contract: `up`, `down`, `verify`, `evidence` — the same shape as
  `gpu-inference`.
- Cost tags (`Project=<name>`, `Ephemeral=true`) wired as provider defaults.
- A stage label (`stage: experiment` → `active` → `archived`) as a repository topic and
  a README banner — work in public is labelled honestly; dead ideas are archived, not
  deleted.

**Visibility rule:** public by default. On GitHub Free, private repositories get neither
rulesets nor environment protection rules — no gate #2 — so a private idea is **rejected
by validation** unless the organization is on a plan that provides both (Team). Never
private without guardrails.

## The idea file (`ideas/<name>.md`)

Front matter is the only machine-read part; the body is for you.

```yaml
---
name: spot-price-tracker        # becomes the repo name; [a-z0-9-], unique
visibility: public              # public | private (private: org on Team plan only)
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

## Decisions

1. **Repo creation: a GitHub App, in a dedicated organization** (decided 2026-11-07). A
   fine-grained personal token would need admin over *every* personal repository and live
   for months; the App has only the permissions listed above, mints hour-long tokens, and
   is fenced to the organization. Apps cannot create repositories in personal accounts,
   which is what forces — and justifies — the organization.
2. **Visibility: public by default** (decided 2026-11-07). Private only once the
   organization is on Team (~$4/user/month), so private never means unguarded.
3. **AWS monthly cap: open** — decided in F2 (suggest $30 while credits last).
4. **Languages: Python (stdlib only) for gates; Go for services** (decided 2026-11-07).
   Gate scripts run on hosted runners with no build step and no dependencies to
   compromise. Anything long-running — a `factory` CLI, the operator agent — is Go.
   Bash only as glue between steps, never for logic.

## Next: fully automatic, safe by construction

First end-to-end run (2026-11-09): an idea typed in the Claude app became factory PR
#5, was merged on a phone, and `ideafactory-labs/sky-hoppers` was created with every
guardrail. Building still needs a manual session. The target loop is: **say the idea →
merge → play the preview → merge.**

| Step | What happens automatically | Phase |
|---|---|---|
| Build starts on merge | Repo creation opens a "build the smallest useful version" issue; the Claude GitHub Action builds and opens a PR | F1.2 |
| Agent fixes its own red CI | A failed check on an agent PR re-invokes the agent, a bounded number of times | F1.3 |
| Preview + evidence on every PR | Playwright screenshot/short video and a playable preview link posted on the PR | F1.4 |
| One status page | Every idea: stage, latest PR, preview, spend | F1.5 |
| Guardrail reconciler | Hourly: every repo in the org has its guardrails, or is archived and reported — whoever created it | F1.6 |

### Safety rules for automation

Threat model: nobody outside can drive the factory App (its key is usable only by
workflows on `main`, which only the owner can change). The realistic risks are a bug, a
confused agent, or injected text steering an agent. Each rule below holds against those.

| # | Rule | Enforced by | Verified by |
|---|---|---|---|
| S1 | No dollar is spent without the owner's approval | cloud credentials exist only via OIDC into the `live` environment (owner is required reviewer); no keys anywhere | TLA+ over every actor → credential path; IAM Access Analyzer on the boundary (F2) |
| S2 | Only the owner merges to `main` | `main` + `only admin merges` rulesets; the build agent authenticates as its own App, not as the owner | empirical: an agent attempts to merge its own PR and must be refused — run on every template change |
| S3 | No secret is reachable by unmerged code | agent credentials live in an `agent` environment restricted to `main` — never org- or repo-wide secrets; policy lint rejects workflows reading secrets outside an environment | lint + reconciler audit |
| S4 | No project is ever unguarded | all-or-nothing creation; reconciler archives any unguarded repo, including ones created outside the factory | failure-injection tests; TLA+ of creation + reconciler |
| S5 | Nothing is deleted | factory code archives, never deletes (lint bans delete calls); org setting: members cannot delete repositories; 90-day owner restore as the net | lint; reconciler reports any repo count drop |
| S6 | Agent effort is bounded | per-run turn and time limits, one agent run per repo at a time, plan usage limits with paid overage off | workflow lint on limits |
| S7 | Only the owner and the factory bot can start an agent | trigger filters on actor; forks and strangers' comments ignored | empirical: a comment from another account must not start a run |

**Least privilege, staged.** GitHub's "Administration: write" also allows deleting
repositories; there is no write-without-delete. Today S5 covers that in code and org
settings. Once building is automatic, the factory App splits in two: a **creator**
(administration, used only during repository creation) and a **builder** (contents and
pull requests only, for everything after) — each job holding only what it needs.

**Formal verification gates F2.** No AWS automation ships until S1, S4 and the F2
boundary rules are model-checked or proved.

## Verification: formal where it must never break, empirical everywhere

- **Empirical** (every PR): unit tests, workflow policy, actionlint, shellcheck, and
  failure-injection tests that prove all-or-nothing creation with a fake `gh`. Each
  check is shown failing on a deliberately broken variant before it is trusted.
- **Formal** (the few invariants that must never break):
  - *A project repository is never reachable without its guardrails* — a TLA+ model of
    `create_project.sh` (every crash point, two merges at once), model-checked by TLC
    on every PR (F1).
  - *No project role can touch IAM, other regions or non-allowlisted instance types* —
    proved with IAM Access Analyzer custom policy checks (automated reasoning) on the
    permissions boundary (F2).
- Each formal check names the code it covers and the commit it was last confirmed
  against, and says what it does not cover. (Approach from pstack's formal-verification
  skills by Lauren Tan.)
