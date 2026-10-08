---
name: stepstone-search
version: 1.0.0
description: >
  Use this skill to search live job listings across Germany on StepStone (stepstone.de),
  one of the largest professional job boards in Germany. Covers full-time, working
  student (Werkstudent), internship, and graduate positions across technology, data,
  engineering, finance, and operations. Trigger phrases: stepstone jobs, search stepstone,
  stellenangebote stepstone, find a job on stepstone, "are there any jobs on stepstone",
  look up this stepstone posting.
context: fork
enabled: true
allowed-tools: Bash(bun run .agents/skills/stepstone-search/cli/src/cli.ts *)
---

# StepStone Search Skill

Search live job listings from **StepStone Germany** (`stepstone.de`). Zero external runtime dependencies — runs directly with `bun`. Automatically extracts Schema.org `JobPosting` metadata including verified publication dates, hiring companies, and full descriptions.

## When to use this skill

- Search for open positions in Germany or specific cities on StepStone
- Filter by recency (e.g. 1 day / 24 hours, 2 days, 7 days)
- Fetch full job description and requirements for a specific posting

## Commands

### Search job listings

```bash
bun run .agents/skills/stepstone-search/cli/src/cli.ts search --query "<title>" [flags]
```

Key flags:
- `--query <text>` / `-q <text>` — keyword or job title (e.g. `"Data Engineer"`).
- `--location <text>` / `-l <text>` — location in Germany (default: `"Deutschland"`).
- `--jobage <days>` — max posting age in days (`1` for <24h, `2` for <48h, `7` for <7d).
- `--page <n>` — 1-indexed page number (default: `1`).
- `--limit <n>` / `-n <n>` — result limit (default: `20`).
- `--format json|table|plain` — output format (default: `json`).

### Fetch full job detail

```bash
bun run .agents/skills/stepstone-search/cli/src/cli.ts detail <url> [--format json|plain]
```

Pass the StepStone job posting URL. Extracts clean Schema.org `JobPosting` data with full description.

## Usage examples

```bash
# Data Engineer roles in Germany, last 2 days
bun run .agents/skills/stepstone-search/cli/src/cli.ts search -q "Data Engineer" -l "Deutschland" --jobage 2 --format table

# Full details for a posting
bun run .agents/skills/stepstone-search/cli/src/cli.ts detail "https://www.stepstone.de/stellenangebote--Geospatial-Solutions-Data-Engineer-m-w-d-Giessen-Vereinigte-Hagelversicherung-VVaG--14425662-inline.html" --format plain
```

## Output formats

| Format | Description |
|---|---|
| `json` | Programmatic JSON output `{ meta: { count, page }, results: [ ... ] }` |
| `table` | Tabular summary for console scanning |
| `plain` | Text summary for inspection |
