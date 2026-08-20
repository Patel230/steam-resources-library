# Deployment and audit implementation pack

## 1. Exact GitHub Pages workflow

Save this as `.github/workflows/deploy-pages.yml`. It assumes the repository builds the Vite site into `dist/` and that the Vite production base is already configured as `/steam-resources-library/`.

```yaml
name: Deploy STEAM Resources Library to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 10.4.1
          run_install: false

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: pnpm

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Build site
        run: pnpm build

      - name: Configure GitHub Pages
        id: pages
        uses: actions/configure-pages@v5

      - name: Upload Pages artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./dist

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    permissions:
      contents: read
      pages: write
      id-token: write
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

The workflow permissions are necessary but may not be sufficient when the repository has never had a Pages site initialized. The owner should first open **Settings → Pages**, choose **GitHub Actions** under **Build and deployment**, and save. If organization policy controls Actions or environments, an organization owner must also allow Pages deployments and remove any blocking reviewer or branch rule from the `github-pages` environment.

Do not add a personal access token to this workflow unless the GitHub API still refuses to initialize Pages after the Settings change. If a stronger credential is genuinely necessary, store it as a repository secret, restrict it to the minimum administrative scope, and never print it or commit it.

## 2. Policy-safe OneDrive audit commands

The commands below are deliberately bounded and anonymous. They treat the official BdMO page as the provenance anchor, do not log in, do not bypass access controls, and do not execute downloaded files. Replace the URL only with the official link published by the BdMO page.

```bash
set -euo pipefail

ROOT="$PWD/bdmo-audit-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$ROOT"/{raw,files,text,logs}
AUDIT="$ROOT/audit.csv"

printf '%s\n' \
  'source_page,shared_url,item_url,item_name,http_status,content_type,bytes,sha256,pdf_pages,text_chars,english_score,substantive_score,decision,reason' \
  > "$AUDIT"

SOURCE_PAGE='https://matholympiad.org.bd/bdmo-questions'
SHARED_URL='https://1drv.ms/f/c/6cf3550aa243dd42/EkLdQ6IKVfMggGxfXgAAAAABEURUqO0NJsvXlmX5nqb2Jg?e=RK3yZd'

# 1. Verify the official provenance page only.
curl --fail --location --silent --show-error --max-time 20 \
  --proto '=https' --tlsv1.2 \
  -A 'STEAM-Resources-Library-audit/1.0' \
  "$SOURCE_PAGE" > "$ROOT/raw/bdmo-source.html"

# 2. Fetch the public shared-folder landing page anonymously.
#    A login page, CAPTCHA, repeated redirect, timeout, or non-HTML response is a boundary: stop.
curl --fail --location --silent --show-error --max-time 20 \
  --proto '=https' --tlsv1.2 \
  -A 'STEAM-Resources-Library-audit/1.0' \
  "$SHARED_URL" > "$ROOT/raw/onedrive-landing.html"

# 3. Extract only visible HTTPS links from the saved page; do not invoke scripts or APIs.
grep -Eo 'https://[^" <>]+' "$ROOT/raw/onedrive-landing.html" \
  | sed 's/[&<].*$//' \
  | sort -u > "$ROOT/visible-links.txt"

# 4. Review the link list manually before downloading. Continue only with direct,
#    public PDF/document URLs that are visibly associated with BdMO files.
sed -n '1,120p' "$ROOT/visible-links.txt"

# 5. For each manually approved direct public URL, set ITEM_URL and ITEM_NAME and run:
ITEM_URL='https://REPLACE-WITH-A-DIRECT-PUBLIC-FILE-URL'
ITEM_NAME='REPLACE-WITH-VISIBLE-BDMO-FILENAME.pdf'
SAFE_NAME="$(printf '%s' "$ITEM_NAME" | tr -cd 'A-Za-z0-9._-')"
OUT="$ROOT/files/$SAFE_NAME"

curl --fail --location --silent --show-error --max-time 30 \
  --proto '=https' --tlsv1.2 \
  -A 'STEAM-Resources-Library-audit/1.0' \
  "$ITEM_URL" -o "$OUT"

# 6. Validate type and integrity. These commands only inspect data.
FILE_TYPE="$(file -b --mime-type "$OUT")"
BYTES="$(wc -c < "$OUT" | tr -d ' ' )"
SHA256="$(sha256sum "$OUT" | awk '{print $1}')"
PAGES='0'
TEXT_CHARS='0'
if [ "$FILE_TYPE" = 'application/pdf' ] && pdfinfo "$OUT" > "$ROOT/logs/$SAFE_NAME.pdfinfo" 2>&1; then
  PAGES="$(awk '/^Pages:/ {print $2}' "$ROOT/logs/$SAFE_NAME.pdfinfo")"
  pdftotext -enc UTF-8 "$OUT" "$ROOT/text/$SAFE_NAME.txt" || true
  TEXT_CHARS="$(wc -m < "$ROOT/text/$SAFE_NAME.txt" | tr -d ' ' )"
else
  printf '%s\n' 'REJECT: not a readable PDF' >> "$ROOT/logs/decisions.log"
fi

# 7. Use heuristic scores only as triage. A human must inspect every kept file.
ENGLISH_SCORE="$(python3 - "$ROOT/text/$SAFE_NAME.txt" <<'PY'
import re, sys
p=sys.argv[1]
try: text=open(p,encoding='utf-8',errors='ignore').read()
except OSError: text=''
words=re.findall(r"[A-Za-z]+", text)
markers=sum(bool(re.search(rf'\\b{w}\\b', text, re.I)) for w in ['Question','Problem','Solution','Answer','Choose','Prove','Find','Compute'])
print(min(100, round(100*len(words)/max(1,len(text.split()))*0.85)))
PY
)"
SUBSTANTIVE_SCORE="$(grep -Eio 'question|problem|solution|answer|prove|compute|find|multiple choice|olympiad' "$ROOT/text/$SAFE_NAME.txt" 2>/dev/null | wc -l | tr -d ' ' )"

# 8. Human decision gate. Do not automatically add catalog rows from these scores.
#    Keep only when the visible file is first-party, public, free, English, and substantive.
DECISION='REVIEW'
REASON='Manual review required: inspect actual questions, language, provenance, and duplicates.'

printf '%s\n' \
  "$(python3 - "$SOURCE_PAGE" "$SHARED_URL" "$ITEM_URL" "$ITEM_NAME" "$FILE_TYPE" "$BYTES" "$SHA256" "$PAGES" "$TEXT_CHARS" "$ENGLISH_SCORE" "$SUBSTANTIVE_SCORE" "$DECISION" "$REASON" <<'PY'
import csv,sys,io
row=sys.argv[1:]
print(io.StringIO(), end='')
print(','.join('"'+x.replace('"','""')+'"' for x in row))
PY
)" >> "$AUDIT"

printf 'Audit directory: %s\nAudit CSV: %s\n' "$ROOT" "$AUDIT"
```

The `ENGLISH_SCORE` and `SUBSTANTIVE_SCORE` values are triage signals only. They are not admission decisions. A reviewer must open the actual document, confirm that the questions or solutions are clearly English, reject administrative or answer-only material, compare the canonical URL against the catalog, and then replace `REVIEW` with `KEEP` or `REJECT` plus an explicit reason. If the shared folder requires authentication or an access workaround, stop and record `REJECT` with `inaccessible without workaround`; do not attempt to circumvent the restriction.

## 3. Verification after any accepted file

```bash
python3 scripts/build_catalog_index.py
python3 scripts/audit_clean_content.py
pnpm test
pnpm check
pnpm build
```

Only after the complete validation chain passes should an accepted file become a catalog row and a new country chunk be committed.

## References

1. [GitHub — Using custom workflows with GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
2. [GitHub — Use GITHUB_TOKEN for authentication in a workflow](https://docs.github.com/actions/reference/authentication-in-a-workflow)
3. [Bangladesh Mathematical Olympiad — BdMO Questions](https://matholympiad.org.bd/bdmo-questions)
