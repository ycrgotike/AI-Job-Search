---
name: xing-search
version: 1.0.0
description: >
  Use this skill to search live job postings on XING (xing.com / xing.de), the
  leading professional business network in Germany, Austria, and Switzerland (DACH).
  Covers open positions across tech, data engineering, software, AI, and business
  functions. Trigger phrases: xing jobs, search xing, jobs auf xing, stellenangebote
  xing, find jobs on xing, "are there any jobs on xing", look up this xing posting.
context: fork
enabled: true
allowed-tools: Bash(bun run .agents/skills/xing-search/cli/src/cli.ts *)
---

# XING Search Skill

Search live job listings from **XING** (`xing.com` / `xing.de`), the primary professional network in the German-speaking (DACH) region. Zero external runtime dependencies — runs directly with `bun`. Automatically extracts Schema.org `JobPosting` metadata including verified publication dates, hiring companies, and full descriptions.

## When to use this skill

- Search for open positions across Germany or specific cities on XING
- Filter by recency (e.g. last 2 days)
- Fetch full job description and requirements for a specific posting

## Commands

### Search job listings

```bash
bun run .agents/skills/xing-search/cli/src/cli.ts search --query "<title>" [flags]
```

Key flags:
- `--query <text>` / `-q <text>` — keyword or job title (e.g. `"Data Engineer"`).
- `--location <text>` / `-l <text>` — location in Germany (default: `"Deutschland"`).
- `--jobage <days>` — max posting age in days (e.g. `2`).
- `--page <n>` — 1-indexed page number (default: `1`).
- `--limit <n>` / `-n <n>` — result limit (default: `20`).
- `--format json|table|plain` — output format (default: `json`).

### Fetch full job detail

```bash
bun run .agents/skills/xing-search/cli/src/cli.ts detail <url|id> [--format json|plain]
```

Pass the XING job URL or ID. Extracts clean Schema.org `JobPosting` data with full description.

## Usage examples

```bash
# Data Engineer roles in Germany, last 2 days
bun run .agents/skills/xing-search/cli/src/cli.ts search -q "Data Engineer" -l "Deutschland" --jobage 2 --format table

# Full details for a posting
bun run .agents/skills/xing-search/cli/src/cli.ts detail "https://www.xing.com/jobs/augsburg-data-ai-software-engineer-156807261" --format plain
```

## Output formats

| Format | Description |
|---|---|
| `json` | Programmatic JSON output `{ meta: { count, page }, results: [ ... ] }` |
| `table` | Tabular summary for console scanning |
| `plain` | Text summary for inspection |
