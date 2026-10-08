---
name: arbeitsagentur-search
version: 1.0.0
description: >
  Use this skill to search official live German job vacancies from the Federal
  Employment Agency (Bundesagentur für Arbeit / jobboerse.arbeitsagentur.de),
  or to look up full details for a specific posting. Covers all of Germany with
  direct employer data, public administration, engineering, IT, and industry roles.
  Trigger phrases: arbeitsagentur jobs, jobsuche arbeitsagentur, stellenangebote
  bundesagentur, jobs in germany, german federal employment agency, "are there any
  jobs on arbeitsagentur", look up this arbeitsagentur posting.
context: fork
enabled: true
allowed-tools: Bash(bun run .agents/skills/arbeitsagentur-search/cli/src/cli.ts *)
---

# Arbeitsagentur Search Skill

Search official job postings from Germany's Federal Employment Agency (**Bundesagentur für Arbeit** / `arbeitsagentur.de`). Powered by the official public Jobsuche REST API — zero external runtime dependencies, fast structured JSON responses, and no authentication keys required.

## When to use this skill

- Search for job vacancies across Germany or in a specific German city
- Retrieve exact publication dates, company names, locations, and salary brackets
- Fetch full job descriptions and employer requirement details via `referenznummer`

## Commands

### Search job listings

```bash
bun run .agents/skills/arbeitsagentur-search/cli/src/cli.ts search --query "<title>" [flags]
```

Key flags:
- `--query <text>` / `-q <text>` — keyword or job title (e.g. `"Data Engineer"`, `"Softwareentwickler"`).
- `--location <text>` / `-l <text>` — city or region in Germany (e.g. `"Berlin"`, `"Koblenz"`, `"Deutschland"`).
- `--jobage <days>` — filter by recency (e.g. `2` for postings published within the last 48 hours).
- `--page <n>` — 1-indexed result page (default `1`).
- `--limit <n>` / `-n <n>` — cap total results returned (default `20`).
- `--format json|table|plain` — output format (default `json`).

### Fetch full job detail

```bash
bun run .agents/skills/arbeitsagentur-search/cli/src/cli.ts detail <refnr|url> [--format json|plain]
```

Pass either the job's `referenznummer` (e.g. `12265-350002_JB5242033-S`) or full Arbeitsagentur job detail URL. Returns the complete job description, working hours, and employment contract details.

## Usage examples

```bash
# Data Engineer positions in Germany, max 2 days old
bun run .agents/skills/arbeitsagentur-search/cli/src/cli.ts search -q "Data Engineer" -l "Deutschland" --jobage 2 --format table

# Data Analyst positions in Koblenz
bun run .agents/skills/arbeitsagentur-search/cli/src/cli.ts search -q "Data Analyst" -l "Koblenz" --format table

# Full details for a job
bun run .agents/skills/arbeitsagentur-search/cli/src/cli.ts detail "12265-350002_JB5242033-S" --format plain
```

## Output formats

| Format | Description |
|---|---|
| `json` | Programmatic JSON output `{ meta: { count, page }, results: [ ... ] }` |
| `table` | Console tabular view |
| `plain` | Text summary for inspection |
