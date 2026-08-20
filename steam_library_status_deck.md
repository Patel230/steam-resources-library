# STEAM Resources Library — Status, Evidence, and Deployment Readiness

## Slide 1 — STEAM Resources Library
**Global catalog of verified free STEAM learning resources**

Repository status, coverage metrics, GitHub Pages deployment block, and the next evidence-gated expansion step.

**As of:** 20 August 2026

**Repository:** Patel230/steam-resources-library

---

## Slide 2 — What the library promises

The library is an evidence-backed catalog rather than a link dump.

| Admission gate | Required evidence |
| --- | --- |
| First-party | University, ministry, exam board, olympiad, or contest organizer source |
| English-only | Substantive questions, tasks, or solutions visibly available in English |
| Free and public | Reachable without login, paywall, or access workaround |
| Substantive | Actual exams, PYQs, contests, quizzes, assignments, MCQs, problems, or solutions |
| Auditable | Direct URL, resource type, country, track, and verification evidence recorded |

**Policy principle:** never pad country counts when a source is inaccessible, non-English, duplicated, or administrative-only.

---

## Slide 3 — Current catalog snapshot

| Metric | Current value |
| --- | ---: |
| Unique live catalog resources | **1,477** |
| Catalog labels represented | **32** |
| GA assignments | **658** |
| Engineering Mathematics assignments | **596** |
| Discrete Mathematics assignments | **664** |
| Resources classified free | **1,477** |
| Top-100 countries at 100+ records | **7 / 100** |

Counts are generated from the live CSV allowlist after URL deduplication. Track assignments can overlap when one resource covers more than one track.

---

## Slide 4 — Top-100 coverage and honest gaps

| Country | Live records | Position |
| --- | ---: | --- |
| Nigeria | 403 | Above target |
| South Africa | 146 | Above target |
| Canada | 123 | Above target |
| United States | 110 | Above target |
| India | 101 | At target |
| Australia | 100 | At target |
| Malaysia | 100 | At target |
| Thailand | 87 | 13-record gap |
| Philippines | 13 | 87-record gap |
| Bangladesh | 0 | Research/access gap |
| Viet Nam | 0 | Research/access gap |

The next expansion should prioritize population rank, first-party archive availability, English accessibility, and category balance—not merely the largest raw gap.

---

## Slide 5 — Open-source repository readiness

The public repository now includes the MIT license, README guidance, contribution instructions, code of conduct, security policy, bug-report and resource-suggestion issue forms, pull-request guidance, and automated test/build workflows.

The latest maintenance commits are `3e53ffa` and `6f85724`. Local validation passed for catalog-index generation, tests, TypeScript checking, and production build. GitHub Actions validation also passed on commit `6f857246c336eb3974b118720606f6b3d5435bce`.

**Repository:** https://github.com/Patel230/steam-resources-library

---

## Slide 6 — GitHub Pages deployment block

The build succeeds, but Pages deployment stops at `actions/configure-pages@v5` with:

> Resource not accessible by integration

The repository API currently reports `has_pages: false`, and the expected URL returns HTTP 404.

**Manual resolution path:**

1. Open **Repository → Settings → Pages**.
2. Under **Build and deployment**, select **Source: GitHub Actions** and save.
3. Open **Settings → Actions → General** and ensure actions are allowed; set workflow permissions to allow read access to repository contents. The workflow itself grants `pages: write` and `id-token: write`.
4. In **Settings → Environments**, confirm or create the `github-pages` environment and ensure deployment protection rules do not block the repository owner.
5. Re-run the Pages workflow from **Actions → Deploy STEAM Resources Library to GitHub Pages → Run workflow**.
6. Verify the Pages API, the workflow conclusion, and `curl -I -L https://patel230.github.io/steam-resources-library/`.

If the Settings UI cannot enable Pages, use an owner-authorized browser session or a credential with repository administration and Pages management capability. A workflow `GITHUB_TOKEN` with `pages: write` is sufficient to deploy an already-enabled Pages site, but it may not be allowed to create the initial Pages site in this repository configuration.

---

## Slide 7 — Policy-safe Bangladesh archive audit

The official Bangladesh Mathematical Olympiad page links to a public OneDrive folder, but the page is Bengali-facing and the project has already observed OneDrive access limitations.

**Audit protocol:**

1. Treat the official BdMO page as the provenance anchor; do not use mirrors, scraped datasets, social posts, or coaching copies as catalog sources.
2. Resolve the shared folder anonymously in a clean browser session. Do not sign in, bypass a CAPTCHA, request elevated permissions, or use a personal account.
3. Record folder listing metadata only: item name, direct share/download URL, file type, visible year/category, HTTP status, content type, and whether the file downloads without an access workaround.
4. For each candidate PDF, verify integrity, page count, extractable text, English-language evidence, substantive question/solution markers, and duplicate canonical URLs.
5. Reject Bengali-only or mixed-language files when the actual questions are not clearly English; reject notices, schedules, covers, syllabi, answer-only files without usable context, login-gated items, and stalled or inaccessible downloads.
6. Persist every keep/reject decision in a research audit CSV with an explicit reason. Add catalog rows only after direct-file review and clean-content validation.
7. Stop when the endpoint stalls or starts requiring an access workaround. Report the boundary honestly rather than retrying indefinitely or counting the archive as coverage.

**Current status:** no Bangladesh records were added because accessible English substantive files were not yet verified.

---

## Slide 8 — Roadmap and references

**Immediate actions:** enable Pages through repository Settings, rerun the deployment, and verify the live URL; then perform a bounded BdMO archive audit and continue Philippines/Viet Nam research only where first-party English files are directly reachable.

**Performance action:** review the remaining large initial JavaScript chunk while preserving lazy country-chunk loading.

**References**

[1] GitHub, “Using custom workflows with GitHub Pages,” https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages

[2] GitHub, “Use GITHUB_TOKEN for authentication in a workflow,” https://docs.github.com/actions/reference/authentication-in-a-workflow

[3] Bangladesh Mathematical Olympiad, “BdMO Questions,” https://matholympiad.org.bd/bdmo-questions

[4] STEAM Resources Library repository, https://github.com/Patel230/steam-resources-library

[5] GitHub Pages target URL, https://patel230.github.io/steam-resources-library/
