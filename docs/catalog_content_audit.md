# Catalog content audit — categorization and type-classification gaps

Generated from every CSV chunk in `apps/web/src/data/` (`118` files), deduplicated by `resource_url`. This is a data audit; it does not edit the catalog.

- **Raw rows:** 3665 deduplicated records
- **Distinct `resource_class` labels:** 88

## Overall inventory

| Track | Records |
|---|---|
| GA | 1851 |
| EM | 1965 |
| DM | 1868 |

| Region | Records |
|---|---|
| Asia | 2004 |
| Africa | 632 |
| Europe | 433 |
| Americas | 416 |
| Oceania | 143 |
| Global / non-roster | 37 |

## Resource-type families (record-level classification)

| Type family | Records |
|---|---|
| Exam/Paper | 1725 |
| Generic PDF/HTML | 779 |
| Solution/Answer | 627 |
| Contest/Olympiad | 346 |
| Gateway/Archive | 156 |
| Practice/Quiz/Assign | 31 |
| Problem set | 1 |

## The classification gap

**779 records** (21% of the catalog) carry the generic `PDF resource` class and are not yet classified by type.

By country:
- India: 654
- United Kingdom: 118
- Canada: 4
- Germany: 2
- United States: 1

By `source_type` (the strongest reclassification signal):
- exam archive: 609
- contest archive: 124
- Olympiad archive: 45
- admissions practice: 1

Suggested class by `source_type` (see worklist CSV):
- `Past year question paper`: 609
- `Contest paper`: 124
- `Olympiad problem`: 45
- `Practice and quizzes`: 1

## Reclassification worklist

Per-record suggestions are in [`pdf_resource_reclassification_worklist.csv`](./pdf_resource_reclassification_worklist.csv) — `779` rows with URL, title, country, track, source, and a suggested `resource_class`. These are **suggestions for audit confirmation**, not automatic edits.

## How to apply (manual, per the quality policy)

1. Open each row's `resource_url`, confirm it is first-party, free, English-facing, and substantive.
2. Assign the fine-grained `resource_class` that fits (e.g. `Past year question paper`, `PDF solution/answer`, `Contest paper`, `Olympiad problem`, `University examination`).
3. Set `free_resource` (`yes`/no) on legacy rows that omit it — see the access gap in the tables above.
4. Update the owning CSV chunk (India + UK dominate this set) and regenerate `catalogIndex.ts` via `scripts/build_catalog_index.py`.

Regenerating the index and re-running `pnpm test` / `pnpm run check` closes the loop.