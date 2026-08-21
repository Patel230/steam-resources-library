#!/usr/bin/env bash
# Read-only GitHub Pages and local build verifier.
# Usage: scripts/verify_github_pages.sh [OWNER/REPO] [SITE_URL]
set -uo pipefail

REPO="${1:-Patel230/steam-resources-library}"
SITE_URL="${2:-https://patel230.github.io/steam-resources-library/}"
WORKFLOW="deploy-pages.yml"
EXPECTED_BRANCH="main"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
REPORT_DIR="${ROOT}/.github-pages-audit"
REPORT="${REPORT_DIR}/report.txt"
FAILURES=0
WARNINGS=0

mkdir -p "$REPORT_DIR"
: > "$REPORT"

say() { printf '%s\n' "$*" | tee -a "$REPORT"; }
pass() { say "PASS  $*"; }
warn() { WARNINGS=$((WARNINGS + 1)); say "WARN  $*"; }
fail() { FAILURES=$((FAILURES + 1)); say "FAIL  $*"; }
section() { say "\n=== $* ==="; }
command_exists() { command -v "$1" >/dev/null 2>&1; }

section "Inputs"
say "Repository: $REPO"
say "Expected branch: $EXPECTED_BRANCH"
say "Site URL: $SITE_URL"
say "Checkout root: $ROOT"
say "Report: $REPORT"

section "Required tools"
for tool in git gh curl jq; do
  if command_exists "$tool"; then pass "$tool is available"; else fail "$tool is required"; fi
done
if ! command_exists gh; then
  say "GitHub CLI is unavailable; cannot continue with API checks."
  exit 2
fi
if ! gh auth status >/dev/null 2>&1; then
  fail "GitHub CLI is not authenticated; run gh auth login"
else
  pass "GitHub CLI is authenticated"
fi

section "Local repository"
if [ -d "$ROOT/.git" ]; then pass "Git checkout detected"; else fail "Not inside a Git checkout"; fi
BRANCH="$(git branch --show-current 2>/dev/null || true)"
if [ "$BRANCH" = "$EXPECTED_BRANCH" ]; then pass "Current branch is $BRANCH"; else warn "Current branch is '${BRANCH:-detached}', expected $EXPECTED_BRANCH"; fi
REMOTE="$(git remote get-url origin 2>/dev/null || true)"
if [ -n "$REMOTE" ]; then pass "origin remote: $REMOTE"; else fail "origin remote is missing"; fi
if [ -z "$(git status --porcelain 2>/dev/null)" ]; then pass "Working tree is clean"; else warn "Working tree has uncommitted changes"; fi
LOCAL_SHA="$(git rev-parse HEAD 2>/dev/null || true)"
REMOTE_SHA="$(git ls-remote origin "refs/heads/${EXPECTED_BRANCH}" 2>/dev/null | awk '{print $1}')"
if [ -n "$LOCAL_SHA" ] && [ "$LOCAL_SHA" = "$REMOTE_SHA" ]; then pass "Local HEAD matches origin/$EXPECTED_BRANCH ($LOCAL_SHA)"; else warn "Local HEAD ($LOCAL_SHA) differs from origin/$EXPECTED_BRANCH ($REMOTE_SHA)"; fi

section "Repository API"
REPO_JSON="$(gh api "repos/$REPO" 2>/dev/null | sed -E $'s/\\x1B\\[[0-9;]*[[:alpha:]]//g' || true)"
if [ -n "$REPO_JSON" ]; then
  VISIBILITY="$(jq -r '.visibility // "unknown"' <<<"$REPO_JSON")"
  DEFAULT_BRANCH="$(jq -r '.default_branch // "unknown"' <<<"$REPO_JSON")"
  if [ "$VISIBILITY" = public ]; then pass "Repository is public"; else warn "Repository visibility is $VISIBILITY"; fi
  if [ "$DEFAULT_BRANCH" = "$EXPECTED_BRANCH" ]; then pass "Default branch is $DEFAULT_BRANCH"; else warn "Default branch is $DEFAULT_BRANCH, expected $EXPECTED_BRANCH"; fi
else
  fail "Cannot read repository API: $REPO"
fi

section "Workflow file"
WORKFLOW_PATH="$ROOT/.github/workflows/$WORKFLOW"
if [ -f "$WORKFLOW_PATH" ]; then
  pass "Found $WORKFLOW_PATH"
  for required in 'actions/configure-pages@v5' 'actions/upload-pages-artifact@v3' 'actions/deploy-pages@v4' 'pages: write' 'id-token: write' 'needs: build' 'github-pages'; do
    if grep -Fq "$required" "$WORKFLOW_PATH"; then pass "Workflow contains: $required"; else fail "Workflow is missing: $required"; fi
  done
else
  fail "Missing $WORKFLOW_PATH"
fi

section "Pages API"
PAGES_HTTP="$(mktemp)"
PAGES_JSON="$(gh api "repos/$REPO/pages" 2>"$PAGES_HTTP" | sed -E $'s/\\x1B\\[[0-9;]*[[:alpha:]]//g' || true)"
if [ -n "$PAGES_JSON" ] && jq -e . >/dev/null 2>&1 <<<"$PAGES_JSON" && ! jq -e '(.message == "Not Found") or (.status == "404")' >/dev/null 2>&1 <<<"$PAGES_JSON"; then
  PAGES_STATUS="$(jq -r '.status // "unknown"' <<<"$PAGES_JSON")"
  PAGES_URL="$(jq -r '.html_url // empty' <<<"$PAGES_JSON")"
  pass "Pages API returned a site object (status: $PAGES_STATUS)"
  [ -n "$PAGES_URL" ] && say "Pages API URL: $PAGES_URL"
else
  API_ERROR="$(tr '\n' ' ' < "$PAGES_HTTP")"
  fail "Pages API did not return a site object: ${API_ERROR:-HTTP error or permission denied}"
fi
rm -f "$PAGES_HTTP"

section "Latest Actions runs"
RUNS_JSON="$(gh api "repos/$REPO/actions/runs?per_page=20" 2>/dev/null | sed -E $'s/\\x1B\\[[0-9;]*[[:alpha:]]//g' || true)"
if [ -n "$RUNS_JSON" ] && jq -e .workflow_runs >/dev/null 2>&1 <<<"$RUNS_JSON"; then
  PAGES_RUN="$(jq -c '[.workflow_runs[] | select(.path == ".github/workflows/'"$WORKFLOW"'")] | sort_by(.created_at) | last // empty' <<<"$RUNS_JSON")"
  if [ -n "$PAGES_RUN" ] && [ "$PAGES_RUN" != null ]; then
    RUN_ID="$(jq -r '.id' <<<"$PAGES_RUN")"
    RUN_STATUS="$(jq -r '.status' <<<"$PAGES_RUN")"
    RUN_CONCLUSION="$(jq -r '.conclusion // "pending"' <<<"$PAGES_RUN")"
    RUN_SHA="$(jq -r '.head_sha' <<<"$PAGES_RUN")"
    say "Latest Pages run: $RUN_ID ($RUN_STATUS/$RUN_CONCLUSION, $RUN_SHA)"
    if [ "$RUN_STATUS" = completed ] && [ "$RUN_CONCLUSION" = success ]; then pass "Latest Pages workflow succeeded"; else fail "Latest Pages workflow is $RUN_STATUS/$RUN_CONCLUSION"; fi
    if [ -n "$LOCAL_SHA" ] && [ "$RUN_SHA" != "$LOCAL_SHA" ]; then warn "Latest Pages run SHA differs from local HEAD"; fi
    RUN_URL="$(jq -r '.html_url' <<<"$PAGES_RUN")"
    say "Run URL: $RUN_URL"
  else
    warn "No Pages workflow run found"
  fi
  CI_RUN="$(jq -c '[.workflow_runs[] | select(.name | test("Validate|CI"))] | sort_by(.created_at) | last // empty' <<<"$RUNS_JSON")"
  if [ -n "$CI_RUN" ] && [ "$CI_RUN" != null ]; then
    CI_STATUS="$(jq -r '.status' <<<"$CI_RUN")"
    CI_CONCLUSION="$(jq -r '.conclusion // "pending"' <<<"$CI_RUN")"
    if [ "$CI_STATUS" = completed ] && [ "$CI_CONCLUSION" = success ]; then pass "Latest CI validation succeeded"; else warn "Latest CI validation is $CI_STATUS/$CI_CONCLUSION"; fi
  fi
else
  fail "Cannot read Actions runs API"
fi

section "Local build output"
if command_exists pnpm && [ -f "$ROOT/package.json" ]; then
  if [ "${RUN_BUILD:-0}" = 1 ]; then
    if (cd "$ROOT" && GITHUB_PAGES=true pnpm build) >>"$REPORT" 2>&1; then pass "Local production build succeeded"; else fail "Local production build failed; see $REPORT"; fi
  else
    warn "Local build not run; set RUN_BUILD=1 to execute pnpm build"
  fi
else
  warn "pnpm or package.json unavailable; local build checks skipped"
fi

ARTIFACT_DIR="${ARTIFACT_DIR:-$ROOT/apps/web/dist/public}"
if [ -d "$ARTIFACT_DIR" ]; then
  if [ -s "$ARTIFACT_DIR/index.html" ]; then pass "Artifact contains $ARTIFACT_DIR/index.html"; else fail "Artifact is missing a non-empty index.html: $ARTIFACT_DIR"; fi
  if [ -s "$ARTIFACT_DIR/404.html" ]; then pass "Artifact contains SPA fallback 404.html"; else warn "Artifact has no 404.html; deep links may 404"; fi
else
  warn "Artifact directory not found: $ARTIFACT_DIR"
fi

section "Base path and live URL"
if [ -s "$ARTIFACT_DIR/index.html" ]; then
  if grep -Eq 'steam-resources-library|/assets/' "$ARTIFACT_DIR/index.html"; then pass "Generated HTML contains production asset/base-path references"; else warn "Generated HTML does not visibly contain the expected project base path"; fi
fi
HEADERS="$(mktemp)"
HTTP_CODE="$(curl -L --max-time 30 --silent --show-error -D "$HEADERS" -o /dev/null -w '%{http_code}' "$SITE_URL" 2>/dev/null || true)"
if [[ "$HTTP_CODE" =~ ^2|^3 ]]; then pass "Live URL returned HTTP $HTTP_CODE"; else fail "Live URL returned HTTP ${HTTP_CODE:-request failure}"; fi
say "Live response headers:"
sed -n '1,12p' "$HEADERS" | tee -a "$REPORT"
rm -f "$HEADERS"

section "Summary"
say "Failures: $FAILURES"
say "Warnings: $WARNINGS"
if [ "$FAILURES" -gt 0 ]; then
  say "RESULT: FAIL — inspect $REPORT"
  exit 1
elif [ "$WARNINGS" -gt 0 ]; then
  say "RESULT: PASS WITH WARNINGS — inspect $REPORT"
  exit 0
else
  say "RESULT: PASS"
  exit 0
fi
