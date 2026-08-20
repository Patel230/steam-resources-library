# GA / EM / DM Resource Hub — Design Brief

## Approach 1: Archive Desk

**Theme Name:** Archive Desk

**Very Brief Intro:** A warm, editorial research interface that feels like a well-kept exam archive: paper textures, ink tones, annotated dividers, and calm density. It makes a large catalog feel considered rather than overwhelming.

**Probability:** 0.07

## Approach 2: Signal Atlas

**Theme Name:** Signal Atlas

**Very Brief Intro:** A high-contrast cartographic system for navigating hard questions across countries and disciplines. It uses a dark ink field, bright signal colors, and an asymmetric atlas layout to turn browsing into a sense of discovery.

**Probability:** 0.08

## Approach 3: Campus Commons

**Theme Name:** Campus Commons

**Very Brief Intro:** A bright, institutional study space with modular cards, friendly color blocks, and a public-library sensibility. It prioritizes approachability and quick scanning for students who are new to the resource landscape.

**Probability:** 0.04

## Chosen Direction: Signal Atlas

### Design Movement

The site follows **neo-editorial information design** with cues from archival atlases, field notebooks, and contemporary museum wayfinding. The visual language should feel scholarly but energetic: serious about provenance, optimistic about exploration.

### Core Principles

1. **Map before maze.** Every surface should answer where the learner is, what they are looking at, and what to do next.
2. **Trust is visible.** Official sources, verification state, and resource type are first-class information, not hidden metadata.
3. **Density with breathing room.** The catalog can be information-rich without becoming a wall of tiny text; whitespace separates concepts, not records.
4. **Every click should orient.** Hover, focus, filter, and open states should reveal the next useful decision without theatrical motion.

### Color Philosophy

The base is a nearly-black **atlas ink** rather than pure black, paired with warm mineral paper for reading surfaces. A signature **signal saffron** highlights discovery, while **copper coral** marks urgency or active states. Desaturated teal and chalk blue distinguish GA, EM, and DM without turning the interface into a rainbow. The palette is intentionally bibliographic: ink for authority, paper for comprehension, saffron for the moment a path becomes visible.

### Layout Paradigm

Use an asymmetric atlas layout. A persistent left navigation rail frames the subject system, while the main canvas moves from a wide “field note” hero into a two-column browse area: a narrow filter column and a flexible result canvas. Resource cards should align to a strong left edge but vary in content length and metadata emphasis, like annotated index cards rather than uniform SaaS tiles.

### Signature Elements

1. A small **coordinate marker** motif: four-point marks and short rules that echo map legends.
2. A **subject triad** system: GA, EM, and DM each have a color tab, a one-line definition, and a distinct glyph.
3. A thin **verified source ribbon** on cards, using a saffron dot and “official” label instead of generic badges.

### Interaction Philosophy

Interactions should feel like turning a page or tracing a route. Filters update the result count immediately, chips can be removed with one action, and cards reveal the source and format without requiring a modal. Keyboard users should be able to focus the search field and filter controls without animation delay. Empty states should teach the user how to recover.

### Animation

Use short 160–220ms transitions with a strong ease-out. Cards rise by 3px and brighten slightly on hover; filter drawers slide in from the rail on mobile; the result count changes with a quick opacity crossfade. On initial load, stagger only the hero eyebrow, headline, and first result cluster by 50ms. Respect reduced-motion preferences and never animate layout dimensions when a color or opacity transition will communicate the change.

### Typography System

Use **Fraunces** for display headlines and section numerals, with **IBM Plex Sans** for body copy, metadata, controls, and dense tables. Headlines should be expressive but short; body text should remain in the 15–17px range with a readable 1.55 line-height. Use uppercase micro-labels with generous tracking for source status and section names, but keep resource titles in sentence case for scanability.

### Brand Essence

**Positioning:** A provenance-first field guide to the world’s aptitude, engineering mathematics, and discrete mathematics practice resources—built for learners who want the right question, not just more questions.

**Personality:** Exacting, curious, grounded.

### Brand Voice

Headlines are concise and directional. CTAs are verbs that promise orientation, not hype. Microcopy explains the catalog’s limits and provenance plainly.

Example lines:

> Find the next hard question.

> Browse the archive by discipline, country, or exam family.

Avoid generic filler such as “Welcome to our website” or “Get started today.”

### Wordmark & Logo

The mark is a bold **four-point coordinate compass**: two offset brackets intersect to form a small north-star aperture. It is symbol-only, scalable, and legible at favicon size. The wordmark uses a custom-feeling Fraunces treatment with a shortened crossbar on the “A” and generous tracking in “RESOURCE HUB”; it should never be rendered as a default logo lockup.

### Signature Brand Color

**Signal Saffron — `#F2B84B`**. It should appear as a decisive marker: active filter, verified-source dot, selected tab, or key callout—not as a general background wash.

## Implementation Reminder

Every CSS/component/page file should reinforce the Signal Atlas direction: atlas ink, mineral paper, signal saffron, expressive serif display type, IBM Plex Sans UI text, asymmetrical navigation, visible provenance, and restrained route-tracing motion. When in doubt, ask: **Does this make the catalog easier to navigate and trust, or does it merely add decoration?**

## Style Decisions

- The coordinate compass is now a recurring orientation device in section starts, filter controls, result context, and resource inspection—not a hero-only decoration.
- Resource titles are normalized into curated archive entries in the UI; file size and format remain metadata below the title.
- GA, EM, and DM use persistent saffron, teal, and coral markers in subject filters and resource-card ribbons so discipline context survives dense scanning.
- Resource cards must read as annotated archive entries: curated names first, source format and file size only as supporting metadata, with official/free/verified signals visible.
- Dense catalog and ledger surfaces repeat route rules, coordinate marks, source ribbons, and status bands so the atlas metaphor continues beyond the hero.
- Coverage summaries group states by region before the individual ledger rows, making active, caveated, and pending signals scannable at a glance.
- Global navigation behaves as an atlas legend through a persistent orientation rail with subject markers, numbered routes, and a country-directory cue.
- Resource cards expose visible provenance ribbons and source hierarchy before supporting metadata, preserving the annotated-record character in dense browse states.
- Coordinate markers are structural anchors for route context, card identity, pagination, and coverage ledger entries rather than decorative ornaments.
- Dynamic route headlines must remain complete field-guide phrases; route labels are normalized before insertion so grammar never reveals a raw filter variable.
- The persistent orientation rail and compass wordmark are part of the page frame, with numbered wayfinding and recurring cardinal cues rather than a conventional header-only navigation model.
- Export and print surfaces preserve the same provenance-first hierarchy as the live catalog: title, country, subject, material, source, verification date, and public URL remain visible together.
- Desktop navigation is an always-visible atlas legend: numbered routes, a north cue, compass markers, and the directory route remain available beyond the hero.
- Dense result areas retain cartographic grid rules, route captions, and a persistent, interactive GA/EM/DM triad so a first scan distinguishes each record family.
- Signal Saffron remains functional orientation energy: verified-source signals, active GA route markers, selected filters, key numerals, and decisive CTAs rather than general surface decoration.
- The desktop frame uses an always-visible atlas legend rather than relying on the header: it includes a compass cue, numbered routes, GA/EM/DM route markers, a 193-state ledger route, and a visible path to countries below the 100-resource target.
- Signal Saffron (`#F2B84B`) is reserved for orientation decisions: the selected route, verified/free direction, primary action, selected filter, and key navigational numerals. Teal and coral remain functional discipline and access-status signals.
- Dense catalog surfaces foreground active route, subject family, first-party provenance, and selected filter state before decorative treatments.

- The country directory uses an in-flow **atlas route key** in addition to the persistent legend: compass cue, numbered route sequence, active directory state, threshold route, and public-source desk stay visible in the document flow.
- Coverage paper surfaces continue the cartographic system through quiet ledger grids, coordinate registers, region wayfinding, and functional progress rules rather than generic editorial tables.
- Subject imagery is treated as an **archival atlas plate**: diagram grids, route codes, and track-specific GA / EM / DM markers contextualise imagery without reducing legibility.
- Signal Saffron `#F2B84B` is reserved primarily for selected orientation, verified/source cues, critical counts, and primary actions; one display phrase per page may use it for emphasis.
- The Signal Atlas wordmark uses a framed compass aperture and abbreviated coordinate register in headers and footers to strengthen the identity beyond a standard template logo.
- The persistent legend exposes a current-coordinate register, cardinal range, active-route marker, and concise “Here” cue so every route feels located inside one field atlas.
- Dense records use an annotated-entry silhouette: subject-coloured coordinate marker, material label, country route, explicit source line, and compact verification coordinate before supporting metadata.
- Saffron remains reserved for the active map position, verified-source direction, priority counts, and primary calls to action; discipline identity belongs to the GA / EM / DM triad rather than general decorative emphasis.
