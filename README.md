# STEAM Resources Library

A country-organized global library of free, verified, English-facing resources for **Science, Technology, Engineering, Arts, and Mathematics**.

The current foundation is the Mathematics collection, including:

- General Aptitude (GA)
- Engineering Mathematics (EM)
- Discrete Mathematics (DM)

The platform is designed to grow into a broader STEAM discovery system while preserving clear provenance, resource taxonomy, country coverage, and honest gaps.

## Quality policy

Every live catalog record is expected to satisfy the project’s source-quality rules:

1. The source is first-party or organizer-owned whenever possible.
2. The resource is publicly accessible and free to access.
3. The visible content is in English or has English-facing metadata suitable for discovery.
4. The document contains substantive questions, problems, assignments, examinations, quizzes, MCQs, contests, or solutions.
5. Duplicate URLs, cover-only files, syllabi, administrative notices, login-gated resources, paywalled resources, and unsupported mirrors are excluded.
6. Records preserve source URLs, country attribution, subject classification, resource type, access model, verification date, and quality metadata.

## Project structure

This repository is a pnpm-workspace monorepo. Follow the `apps/` / `packages/` boundary: `apps/` hold independently built applications, `packages/` hold shared libraries and tooling.

| Path | Purpose |
|---|---|
| `apps/web/` | React + TypeScript Vite frontend (the GitHub Pages deployable) |
| `apps/web/src/data/` | Verified country resource CSV chunks and generated catalog index |
| `apps/web/src/lib/` | Catalog loading, filtering, and shared utilities |
| `apps/web/src/pages/` | Explorer and country-coverage routes |
| `apps/web/src/components/` | Reusable interface components |
| `apps/api/` | Express + tRPC backend, server procedures, and regression tests |
| `packages/shared/` | Shared constants, types, and errors consumed by both apps |
| `packages/scripts/` | Catalog indexing, audit, and validation scripts |
| `research/` | Local research evidence and audit notes |
| `drizzle/` | Database schema and migrations |

## Local development

Install dependencies with:

```bash
pnpm install
```

Run the development server (API serves the web app via Vite middleware) with:

```bash
pnpm run dev
```

Run the validation suite with:

```bash
pnpm test
pnpm run check
pnpm run build
```

## Catalog workflow

Resource additions should be audited locally, deduplicated, classified using the project schema, added to a country CSV chunk, and then included through the generated lazy-loading index. The clean-content audit and regression tests must pass before a tranche is considered complete.

## Roadmap

The next expansion priorities are to increase verified coverage for the top-100 countries, add more first-party GA, EM, and DM archives, and then extend the same provenance-led workflow to Science, Technology, Engineering, and Arts resources.

## Open-source license and source attribution

This repository is released under the [MIT License](LICENSE). The original resources linked by the catalog remain owned by their respective institutions and organizers. Each catalog record should link back to its original source and respect that source’s access and reuse terms.

The public source repository is [Patel230/steam-resources-library](https://github.com/Patel230/steam-resources-library). Pushes to `main` run the GitHub Pages workflow in `.github/workflows/deploy-pages.yml`. The project site is served at `https://patel230.github.io/steam-resources-library/` after Pages completes its first deployment.
