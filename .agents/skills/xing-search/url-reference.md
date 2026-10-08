# XING Job Search URL Reference

Documentation for querying `xing.com` / `xing.de` job search.

## URL Patterns

### 1. Search Endpoint

- **URL:** `https://www.xing.com/jobs/search?keywords={query}&location={location}`
- Following HTTP redirects (`location: /jobs/search/ki?...`) brings the search results page.
- Job cards contain direct links to `/jobs/{city}-{slug}-{id}`.

### 2. Detail Page Schema

- Detail pages embed Schema.org JSON-LD:
  `<script type="application/ld+json">` with `@type: "JobPosting"`.
- Contains:
  - `title`
  - `datePosted` (ISO 8601 string)
  - `validThrough` (deadline)
  - `hiringOrganization.name`
  - `jobLocation`
  - `description`
