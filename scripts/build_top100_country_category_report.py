from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
DATA = ROOT / 'client/src/data'
ROSTER = ROOT / 'research/top100_country_roster.csv'
OUTPUT = ROOT / 'research/top100_country_category_breakdown.csv'
SUMMARY = ROOT / 'research/top100_country_category_summary.md'


def main() -> None:
    with ROSTER.open(newline='', encoding='utf-8') as handle:
        roster = list(csv.DictReader(handle))
    countries = [row['country'] for row in roster]
    target = set(countries)
    by_country_category: dict[str, Counter[str]] = defaultdict(Counter)
    urls: dict[str, set[str]] = defaultdict(set)
    total_urls: set[str] = set()

    for path in sorted(DATA.glob('*_verified_resources.csv')):
        with path.open(newline='', encoding='utf-8') as handle:
            for row in csv.DictReader(handle):
                if row.get('free_resource', '').strip().lower() != 'yes':
                    continue
                url = row.get('resource_url', '').strip()
                if not url:
                    continue
                categories = {part.strip().upper() for part in row.get('track', '').replace(',', '/').split('/')}
                categories &= {'GA', 'EM', 'DM'}
                if not categories:
                    continue
                for country in [part.strip() for part in row.get('country', '').split('/')]:
                    if country not in target:
                        continue
                    urls[country].add(url)
                    for category in categories:
                        by_country_category[country][category] += 1
                    total_urls.add(url)

    with OUTPUT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['rank', 'country', 'GA', 'EM', 'DM', 'total_unique_free', 'gap_to_100', 'status'])
        for roster_row, country in zip(roster, countries):
            counts = by_country_category[country]
            total = len(urls[country])
            status = 'target met' if total >= 100 else ('active' if total else 'pending')
            writer.writerow([roster_row.get('rank', ''), country, counts['GA'], counts['EM'], counts['DM'], total, max(0, 100-total), status])

    active = sum(1 for country in countries if urls[country])
    target_met = sum(1 for country in countries if len(urls[country]) >= 100)
    category_totals = Counter()
    for counter in by_country_category.values():
        category_totals.update(counter)
    ranked = sorted(((country, len(urls[country])) for country in countries), key=lambda item: (-item[1], item[0]))
    gaps = sorted(((country, len(urls[country])) for country in countries), key=lambda item: (item[1], item[0]))

    lines = [
        '# Top-100 country/category breakdown',
        '',
        f'Generated from all `*_verified_resources.csv` chunks using unique free `resource_url` values. Total top-100 unique free resources: **{sum(len(value) for value in urls.values())}**. Countries with at least one resource: **{active}/100**. Countries at 100 or more: **{target_met}/100**.',
        '',
        '| Category | Unique free resources counted |',
        '|---|---:|',
        f'| GA | {category_totals["GA"]} |',
        f'| EM | {category_totals["EM"]} |',
        f'| DM | {category_totals["DM"]} |',
        '',
        '## Highest coverage',
        '',
        '| Country | Total | GA | EM | DM |',
        '|---|---:|---:|---:|---:|',
    ]
    for country, total in ranked[:15]:
        c = by_country_category[country]
        lines.append(f'| {country} | {total} | {c["GA"]} | {c["EM"]} | {c["DM"]} |')
    lines += ['', '## Largest remaining gaps', '', '| Country | Total | Gap to 100 | GA | EM | DM |', '|---|---:|---:|---:|---:|---:|']
    for country, total in gaps[:20]:
        c = by_country_category[country]
        lines.append(f'| {country} | {total} | {max(0,100-total)} | {c["GA"]} | {c["EM"]} | {c["DM"]} |')
    lines += ['', '> Counts are descriptive, not a claim that every possible resource has been found. The catalog retains only public, free, English, substantive, deduplicated, first-party or explicitly approved source records.', '']
    SUMMARY.write_text('\n'.join(lines), encoding='utf-8')
    print(f'Wrote {OUTPUT}')
    print(f'Wrote {SUMMARY}')
    print(f'Top-100 unique free resources: {sum(len(value) for value in urls.values())}')
    print(f'Countries with resources: {active}/100; target met: {target_met}/100')
    print(f'Category totals: GA={category_totals["GA"]}, EM={category_totals["EM"]}, DM={category_totals["DM"]}')


if __name__ == '__main__':
    main()
