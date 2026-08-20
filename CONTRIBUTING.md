# Contributing to STEAM Resources Library

Thank you for helping build a trustworthy, worldwide library of Science, Technology, Engineering, Arts, and Mathematics resources.

## Project principles

STEAM Resources Library prioritizes resources that are free to access, publicly reachable, substantive, and described in English. Mathematics records currently form the foundation of the library, with General Aptitude (GA), Engineering Mathematics (EM), and Discrete Mathematics (DM) as the active subject tracks.

Contributions must preserve provenance. Prefer the original university, examination body, government, Olympiad organiser, or institutional archive. Do not submit mirrors, commercial aggregators, login-gated files, paywalled material, or links that require a private account.

A record should contain meaningful questions, problems, exercises, solutions, or assessment content. Do not add cover pages, syllabi without questions, timetables, administrative notices, grade sheets, textbook page references without the actual problems, or answer-only material that does not provide substantive learning content. English-only catalog content is required; a document that is merely hosted on an English-language page does not qualify if the document itself is not meaningfully in English.

## Local setup

Use Node.js 22 or a compatible current LTS release and pnpm 10.4.1. From the repository root, install dependencies and start the development server:

```bash
pnpm install --frozen-lockfile
pnpm dev
```

Before opening a pull request, run the same checks used by continuous integration:

```bash
pnpm test
pnpm check
pnpm build
```

The build command validates both the Vite frontend and the server bundle. Do not commit `node_modules`, build output, local environment files, runtime logs, or bulky research artifacts. The repository `.gitignore` contains the current exclusion policy.

## Adding catalog resources

Catalog data is stored in verified CSV chunks under `client/src/data/`. Preserve the established 15-column schema and use one row per direct resource URL. Use the existing chunks as field-value examples rather than inventing new taxonomy labels. After adding a chunk, regenerate the lazy catalog index using the repository’s index builder and confirm that the physical CSV is registered in the runtime loader.

Every proposed record should have local evidence for public access, file integrity, English-visible content, substantive questions or solutions, provenance, and deduplication. Keep the evidence in the local research workspace; bulky research artifacts are intentionally excluded from deployment commits. Never fabricate records, ratings, reviews, testimonials, or source-quality claims.

## Pull requests

Pull requests should explain the country or global track, subject category, source institution, resource type, and validation performed. Include the relevant source URLs and note any access caveats. Keep changes focused, avoid unrelated formatting churn, and update documentation when a workflow or data convention changes.

A maintainer may request revisions when a source is not first-party, a document is not substantive, the language requirement is unclear, the URL is duplicated, or the evidence does not support the proposed classification.

## Issues and security

Use GitHub Issues for catalog corrections, broken links, accessibility concerns, and feature ideas. Do not publish credentials, personal access tokens, private URLs, or sensitive user information in issues or pull requests. For a security concern, contact the repository maintainer privately through GitHub rather than opening a public issue.

## License and attribution

The project is released under the MIT License. Resource copyrights remain with their original publishers. Adding a link to the catalog does not transfer ownership of the linked material; contributors should preserve publisher names, original URLs, and attribution metadata.

## Code of conduct

Contributors are expected to communicate respectfully, make evidence-based claims, and support an inclusive learning environment. Harassment, discriminatory content, deliberate misinformation, fabricated resources, and attempts to bypass access controls are not acceptable.

Thank you for helping make the library more useful without compromising its evidence standards.
