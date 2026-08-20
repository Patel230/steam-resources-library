# GitHub Pages remediation and Bangladesh archive audit guidance

## GitHub Pages: required manual settings and permissions

The failure `Resource not accessible by integration` at `actions/configure-pages@v5`, together with `has_pages: false`, indicates that the repository’s Pages site has not been initialized or the workflow token is not allowed to initialize it. The first fix should be performed by the repository owner or an administrator in the GitHub web interface.

Open **Patel230/steam-resources-library → Settings → Pages**. Under **Build and deployment**, set **Source** to **GitHub Actions** and save. This is the critical initialization step. A deployment workflow can usually deploy an already-enabled Pages site with `GITHUB_TOKEN`, but the token may not be permitted to create the initial Pages site in the current repository configuration.

Then open **Settings → Actions → General**. Confirm that GitHub Actions are allowed for the repository. Keep the workflow permissions least-privilege; **Read repository contents permission** is sufficient for checkout, while the deployment job must explicitly grant `pages: write` and `id-token: write`. The repository workflow should retain an environment named **github-pages**, and the deploy job should depend on the build job through `needs: build` or the equivalent build-job ID.

If an organization policy controls Actions or Pages, an organization owner may need to allow GitHub Actions and permit Pages deployments. If the repository is owned by an organization, also check **Settings → Environments → github-pages** for required reviewers, branch restrictions, or protection rules that could block the owner’s deployment. Remove only the rule that blocks this intended deployment; do not weaken unrelated security controls.

After saving the settings, rerun the Pages workflow from **Actions → Deploy STEAM Resources Library to GitHub Pages → Run workflow**. Verify all three layers: the workflow concludes successfully; the repository Pages endpoint reports an enabled site; and `curl -I -L https://patel230.github.io/steam-resources-library/` returns a successful response rather than 404.

If the Settings UI cannot initialize Pages, use an owner-authorized browser session or an administrative credential with repository administration and Pages-management capability. A personal access token or GitHub App installation token should be used only when necessary, stored as a repository secret, limited to the minimum repository administration or Pages scope required, and never committed to the repository. A normal workflow `GITHUB_TOKEN` with `pages: write` is not guaranteed to have permission to create the initial Pages site.

## Bangladesh Mathematical Olympiad OneDrive: policy-safe audit

Use the official [Bangladesh Mathematical Olympiad questions page](https://matholympiad.org.bd/bdmo-questions) as the provenance anchor. Its linked OneDrive folder is a research lead, not automatic catalog evidence. The page is Bengali-facing, and the project’s admission policy requires English substantive content, public free access, first-party provenance, and direct auditability.

Perform the audit in a clean anonymous browser session. Open the official BdMO page, follow its own OneDrive link, and do not sign in, bypass a CAPTCHA, request permission, use a personal account, or use a mirror or scraped dataset. If the folder cannot be listed or files cannot be downloaded anonymously, record the access failure and stop. Do not retry a stalled endpoint indefinitely.

For every visible candidate file, record a row in an audit table containing the official source page, direct file URL, item name, year, category, HTTP status, content type, file size, download timestamp, checksum, PDF integrity, page count, extracted-text status, English-language evidence, substantive-question evidence, duplicate match, and final keep/reject decision. Keep the audit evidence outside the deployed application unless a small research summary is intentionally committed.

Inspect the actual downloaded file rather than relying on the file name. Confirm that it is a readable PDF or other supported document, that it contains actual questions, problems, MCQs, assignments, contest tasks, or solutions, and that the substantive text is clearly in English. Reject Bengali-only or ambiguous-language files, administrative notices, schedules, covers, syllabi, result sheets, answer-only documents without substantive context, duplicate canonical URLs, login-gated resources, and files that require an access workaround.

Use bounded requests and timeouts. A safe audit sequence is: fetch the official page; resolve the public folder; enumerate visible files; download one candidate at a time with a bounded timeout; validate file type and integrity; extract text; inspect English and substantive markers; deduplicate; persist the decision; then continue. If an endpoint stalls, returns an access challenge, or begins requiring authentication, stop and mark the affected candidates as inaccessible rather than changing the project policy.

Only after a candidate passes every gate should it be converted into a 15-column catalog row, added to the Bangladesh chunk, included in the generated catalog index, and covered by the normal test, clean-content, type-check, and build validation chain.

## References

1. [GitHub — Using custom workflows with GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
2. [GitHub — Use GITHUB_TOKEN for authentication in a workflow](https://docs.github.com/actions/reference/authentication-in-a-workflow)
3. [Bangladesh Mathematical Olympiad — BdMO Questions](https://matholympiad.org.bd/bdmo-questions)
4. [STEAM Resources Library repository](https://github.com/Patel230/steam-resources-library)
