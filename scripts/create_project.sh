#!/usr/bin/env bash
# create_project.sh IDEA_FILE — create one project repository from template/.
#
# Runs only inside .github/workflows/create-project.yml (environment `provision`, branch
# main) with GH_TOKEN = a one-hour GitHub App installation token fenced to $OWNER.
# Every value used here comes from validated front matter (scripts/idea.py) or from
# repository variables; nothing from the idea body reaches this shell.
set -euo pipefail

idea="$1"
: "${OWNER:?}" "${APPROVER:?}" "${GH_TOKEN:?}" "${FACTORY_REPO:?}" "${APP_SLUG:?}"
root="$(cd "$(dirname "$0")/.." && pwd)"

name="$(python3 "$root/scripts/idea.py" field "$idea" name)"
visibility="$(python3 "$root/scripts/idea.py" field "$idea" visibility)"
idea_url="https://github.com/${FACTORY_REPO}/blob/main/ideas/${name}.md"
repo="${OWNER}/${name}"

# Invariant: a project repository never stays reachable without its guardrails.
# Creation is all-or-nothing — if any step after the repo exists fails, the repo is
# archived (read-only, kept for forensics) before this script exits non-zero.
work="$(mktemp -d)"
created=0
finish() {
  status=$?
  rm -rf "$work"
  if [ "$status" -ne 0 ] && [ "$created" -eq 1 ]; then
    echo "::error::guardrails incomplete for ${repo}; archiving it"
    gh api -X PATCH "repos/${repo}" -F archived=true --silent ||
      echo "::error::ARCHIVE FAILED — ${repo} may be unguarded; archive it by hand"
  fi
  exit "$status"
}
trap finish EXIT

echo "::group::create ${repo} (${visibility})"
# Fails loudly if the repo exists: CI's collision check should have caught that, and the
# factory never adopts a repository it did not create.
gh api -X POST "orgs/${OWNER}/repos" \
  -f name="${name}" -f visibility="${visibility}" \
  -f description="factory project — see ${idea_url}" \
  -F has_wiki=false -F has_projects=false -F delete_branch_on_merge=true \
  -F allow_squash_merge=true -F allow_merge_commit=true -F allow_rebase_merge=false \
  --silent
created=1
echo "::endgroup::"

echo "::group::seed from template/"
cp -R "$root/template/." "$work/"
mkdir -p "$work/.factory"
cp "$root/scripts/check_workflows.py" "$work/.factory/check_workflows.py"
# Render *.tmpl. Substituted values are validated names and fixed URLs only.
while IFS= read -r -d '' t; do
  sed -e "s|{{NAME}}|${name}|g" -e "s|{{OWNER}}|${OWNER}|g" \
      -e "s|{{IDEA_URL}}|${idea_url}|g" -e "s|{{FACTORY_REPO}}|${FACTORY_REPO}|g" \
      "$t" > "${t%.tmpl}"
  rm "$t"
done < <(find "$work" -name '*.tmpl' -print0)

bot_id="$(gh api "users/${APP_SLUG}%5Bbot%5D" --jq .id)"
auth="$(printf 'x-access-token:%s' "$GH_TOKEN" | base64 -w0)"
git -C "$work" init -q -b main
git -C "$work" add -A
git -C "$work" -c user.name="${APP_SLUG}[bot]" \
  -c user.email="${bot_id}+${APP_SLUG}[bot]@users.noreply.github.com" \
  commit -q -m "Seed from factory template (idea: ${idea_url})"
git -C "$work" -c http.extraheader="AUTHORIZATION: basic ${auth}" \
  push -q "https://github.com/${repo}.git" main
echo "::endgroup::"

echo "::group::guardrails"
# Stage label, honestly public.
gh api -X PUT "repos/${repo}/topics" -f 'names[]=factory' -f 'names[]=stage-experiment' --silent
# Secret scanning + push protection: a commit containing a credential is rejected.
gh api -X PATCH "repos/${repo}" --silent --input - <<'JSON'
{"security_and_analysis": {"secret_scanning": {"status": "enabled"},
                           "secret_scanning_push_protection": {"status": "enabled"}}}
JSON
# Gate #2: environment `live` — required reviewer, deployable from main only.
approver_id="$(gh api "users/${APPROVER}" --jq .id)"
gh api -X PUT "repos/${repo}/environments/live" --silent --input - <<JSON
{"wait_timer": 0, "prevent_self_review": false,
 "reviewers": [{"type": "User", "id": ${approver_id}}],
 "deployment_branch_policy": {"protected_branches": false, "custom_branch_policies": true}}
JSON
gh api -X POST "repos/${repo}/environments/live/deployment-branch-policies" \
  -f name=main -f type=branch --silent
# Branch protection last, so the seed push above was allowed. Two rulesets: `main`
# binds everyone (PR, green CI, no force-push or deletion); `only admin merges` lets
# only a repository admin update main, and only by merging a PR — agents propose,
# they never merge.
gh api -X POST "repos/${repo}/rulesets" --input "$root/config/ruleset.json" --silent
gh api -X POST "repos/${repo}/rulesets" --input "$root/config/ruleset-only-admin-merges.json" --silent
echo "::endgroup::"

# Pages is a convenience, not a guardrail: failing to enable it warns and continues
# (the repo is fully guarded at this point). Deploys come from template pages.yml.
echo "::group::pages"
if ! gh api -X POST "repos/${repo}/pages" -f build_type=workflow --silent; then
  echo "::warning::could not enable Pages for ${repo} (does the App have Pages: write?)"
fi
echo "::endgroup::"

echo "https://github.com/${repo}"
