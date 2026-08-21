# GitHub Pages manual enablement and verification script

## Exact GitHub Settings clicks

1. Sign in to GitHub with the owner or repository-administrator account that controls `Patel230/steam-resources-library`.
2. Open `https://github.com/Patel230/steam-resources-library`.
3. Select the **Settings** tab. If Settings is not visible, open the repository’s overflow menu and choose **Settings**.
4. In the left sidebar, under **Code and automation**, select **Pages**.
5. In **Build and deployment**, open the **Source** dropdown.
6. Choose **GitHub Actions**. Do not choose “Deploy from a branch,” because this repository’s workflow uploads a Pages artifact and uses `actions/deploy-pages`.
7. Click **Save** if GitHub presents a Save button. If the setting saves immediately, remain on the Pages screen and confirm that the source now reads **GitHub Actions**.
8. In the left sidebar, open **Actions → General**. Confirm that actions are enabled for the repository. If the organization restricts Actions, an organization owner must allow GitHub Actions for this repository.
9. Return to **Settings → Environments**. Confirm that an environment named `github-pages` exists. If it does not, create it with **New environment**, enter `github-pages`, and select **Configure environment**.
10. Inspect the `github-pages` environment for required reviewers, branch restrictions, or deployment protection rules. Remove only rules that block the intended `main`-branch Pages deployment, or approve the deployment when the rule is intentionally retained.
11. Return to **Actions**. Open **Deploy STEAM Resources Library to GitHub Pages**.
12. Use **Run workflow**, select `main`, and click **Run workflow**. Alternatively, push a new commit to `main` after saving the Pages setting.
13. Open the new run and confirm that `Build`, `Configure Pages`, `Upload Pages artifact`, and `Deploy to GitHub Pages` all complete successfully.
14. Open the deployment URL shown in the workflow’s `github-pages` environment. For this repository, the expected URL is `https://patel230.github.io/steam-resources-library/`.

If the Pages screen is unavailable, the account may lack repository administration permission, the repository may be controlled by an organization policy, or Pages may be restricted by an enterprise policy. Escalate to the organization or enterprise owner rather than weakening unrelated security controls.

## GitHub CLI verification

Run these commands after saving the Settings change:

```bash
set -euo pipefail
REPO='Patel230/steam-resources-library'
SHA="$(gh api "repos/$REPO" --jq '.default_branch')"
printf 'default branch: %s\n' "$SHA"

printf '%s\n' '--- repository Pages state ---'
gh api "repos/$REPO/pages" \
  --jq '{status,html_url,source,https_enforced,protected_domain_state}'

printf '%s\n' '--- recent workflow runs ---'
gh run list --repo "$REPO" --workflow deploy-pages.yml --limit 5 \
  --json databaseId,headSha,status,conclusion,url,createdAt,updatedAt

printf '%s\n' '--- latest Pages run ---'
RUN_ID="$(gh run list --repo "$REPO" --workflow deploy-pages.yml --limit 1 \
  --json databaseId --jq '.[0].databaseId')"
if [ -n "$RUN_ID" ]; then
  gh run view "$RUN_ID" --repo "$REPO" \
    --json status,conclusion,headSha,url,jobs
fi

printf '%s\n' '--- HTTP verification ---'
curl -I -L --max-time 20 --silent --show-error \
  'https://patel230.github.io/steam-resources-library/' \
  | sed -n '1,12p'
```

A successful initialization normally changes the Pages API from HTTP 404 / `Not Found` to a JSON object containing `status`, `html_url`, and `source`. The deployment run should show `completed` with `success`, and the final HTTP request should return a successful status such as 200 or a GitHub Pages redirect followed by 200.

## REST API verification without `gh`

```bash
set -euo pipefail
export GH_TOKEN="$(gh auth token)"
REPO='Patel230/steam-resources-library'

curl --fail-with-body --silent --show-error \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  "https://api.github.com/repos/$REPO/pages" \
  | jq '{status,html_url,source,https_enforced,protected_domain_state}'

curl --fail-with-body --silent --show-error \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  "https://api.github.com/repos/$REPO/actions/runs?per_page=10" \
  | jq '[.workflow_runs[] | select(.name == "Deploy STEAM Resources Library to GitHub Pages") | {id,head_sha,status,conclusion,html_url,created_at}]'
```

Do not treat an API 404 as proof that the workflow YAML is wrong. For this incident, the workflow reached `actions/configure-pages@v5`, which then failed while attempting to create the Pages site. That pattern means the repository-level Pages site still needs owner-authorized initialization or a policy change.

## Presentation script

### Slide 1 — The problem in one sentence

“Today we are fixing a repository-level GitHub Pages initialization problem, not a build problem. The STEAM Resources Library code is pushed, CI passes, but the Pages API reports no site and `configure-pages` returns ‘Resource not accessible by integration.’”

### Slide 2 — What the workflow already does

“The workflow checks out `main`, installs dependencies, builds the Vite site, prepares the SPA fallback, uploads the Pages artifact, and deploys it through the `github-pages` environment. Its deploy job has `contents: read`, `pages: write`, and `id-token: write`, and it waits for the build job. Those are the correct least-privilege deployment permissions.”

### Slide 3 — The manual initialization clicks

“Open the repository, choose Settings, then Pages under Code and automation. In Build and deployment, change Source to GitHub Actions and save. This is the important owner-authorized step: a workflow token can deploy a Pages site, but may not be permitted to create the initial site when the Pages API returns `has_pages: false`.”

### Slide 4 — Check Actions and the environment

“Next, open Actions → General and confirm Actions are enabled. Then open Settings → Environments and confirm that `github-pages` exists. If it has required reviewers or branch restrictions, approve or adjust only the rule that blocks the intended `main` deployment. Organization-owned repositories may require an organization owner to change these controls.”

### Slide 5 — Rerun and read the evidence

“Return to Actions, open the Pages workflow, choose Run workflow, select `main`, and start it. A successful run completes Configure Pages, artifact upload, and deployment. The final deployment step displays the Pages URL. The expected URL is `https://patel230.github.io/steam-resources-library/`.”

### Slide 6 — Verify independently with CLI and API

“Use `gh api repos/Patel230/steam-resources-library/pages` and check that the response contains `status`, `html_url`, and `source`. Then inspect the latest workflow run with `gh run view`. Finally, use `curl -I -L` against the expected URL. Success means a populated Pages API response, a completed successful workflow, and a successful HTTP response.”

### Slide 7 — If the error remains

“If `configure-pages` still reports ‘Resource not accessible by integration,’ the remaining issue is administrative or organizational. Confirm that the signed-in account is an owner or repository administrator, that Actions are allowed, that Pages is allowed by organization or enterprise policy, and that the `github-pages` environment is not blocked. Do not add a broad personal access token as a first response.”

### Slide 8 — Close with the operational boundary

“The code is ready and CI is green. The only remaining publication step is owner-authorized Pages initialization. Once the site is live, we can verify the URL and continue catalog expansion without changing the library’s evidence standards.”

## References

1. [GitHub — Using custom workflows with GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
2. [GitHub — REST API: Pages](https://docs.github.com/en/rest/pages/pages)
3. [GitHub — Authentication in a workflow](https://docs.github.com/actions/reference/authentication-in-a-workflow)
