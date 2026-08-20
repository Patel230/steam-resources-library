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

| Path | Purpose |
|---|---|
| `client/` | React and TypeScript frontend |
| `client/src/data/` | Verified country resource CSV chunks and generated catalog index |
| `client/src/lib/` | Catalog loading, filtering, and shared utilities |
| `client/src/pages/` | Explorer and country-coverage routes |
| `client/src/components/` | Reusable interface components |
| `server/` | Server procedures and regression tests |
| `scripts/` | Catalog indexing, audit, and validation scripts |
| `research/` | Local research evidence and audit notes; excluded from deployment checkpoints when configured |
| `drizzle/` | Database schema and migrations |

## Local development

Install dependencies with:

```bash
pnpm install
```

Run the development server with:

```bash
pnpm run dev
```

Run the validation suite with:

```bash
pnpm test
pnpm exec tsc --noEmit
pnpm run build
```

## Catalog workflow

Resource additions should be audited locally, deduplicated, classified using the project schema, added to a country CSV chunk, and then included through the generated lazy-loading index. The clean-content audit and regression tests must pass before a tranche is considered complete.

## Roadmap

The next expansion priorities are to increase verified coverage for the top-100 countries, add more first-party GA, EM, and DM archives, and then extend the same provenance-led workflow to Science, Technology, Engineering, and Arts resources.

## License and source attribution

This repository is an indexing and discovery application. The original resources remain owned by their respective institutions and organizers. Each catalog record should link back to its original source and respect that source’s access and reuse terms.
