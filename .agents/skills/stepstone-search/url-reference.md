# StepStone Germany URL Reference

Documentation for querying `stepstone.de` without credentials or external scrapers.

## URL Patterns

### 1. Search Endpoint

- **URL Pattern:** `https://www.stepstone.de/jobs/{query_slug}/in-{location_slug}`
  - Example: `https://www.stepstone.de/jobs/data-engineer/in-deutschland`
- **Recency Parameter:**
  - `?ag=age_1`: Filter for postings newer than 24 hours
  - `?ag=age_7`: Filter for postings newer than 7 days
- **Pagination Parameter:**
  - `?page={page}`: 1-indexed page number

### 2. Search Card Markup

- Job links follow the pattern:
  `href="/stellenangebote--{Title}-{City}-{Company}--{ID}-inline.html"`
- Title text is nested within the anchor element.

### 3. Detail Page Schema

- Detail URLs render Schema.org JSON-LD:
  `<script type="application/ld+json">` with `@type: "JobPosting"`.
- Contains:
  - `title`
  - `datePosted` (ISO 8601 string)
  - `validThrough` (deadline)
  - `hiringOrganization.name`
  - `employmentType`
  - `description` (HTML / plain text)
