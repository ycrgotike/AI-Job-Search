# Arbeitsagentur Jobsuche API Reference

Documentation of the Bundesagentur für Arbeit (BA) Jobsuche REST API endpoints used by `arbeitsagentur-search`.

## Base URL & Authentication

- **Base URL:** `https://rest.arbeitsagentur.de/jobboerse/jobsuche-service`
- **Header:** `X-API-Key: jobboerse-jobsuche`
- **Client ID:** `jobboerse-jobsuche` (public key from Bundesagentur für Arbeit OpenAPI specification, api.bund.dev)
- **User-Agent:** `Mozilla/5.0 (compatible; arbeitsagentur-cli/1.0)`

## Endpoints

### 1. Job Search

- **Path:** `/pc/v6/jobs`
- **Method:** `GET`
- **Parameters:**
  - `was`: Keywords or Job Title (e.g. `Data Engineer`)
  - `wo`: Location (e.g. `Deutschland`, `Berlin`)
  - `page`: Page number (1-indexed)
  - `size`: Results per page (e.g. 25, 50)
  - `veroeffentlichtseit`: Optional filter for publication age in days (0–100)
- **Response Structure:**
  - `ergebnisliste`: Array of job objects
    - `referenznummer`: string (unique ID e.g. `12265-350002_JB5242033-S`)
    - `stellenangebotsTitel`: string (e.g. `Data Engineer (m/w/d)`)
    - `firma`: string (company name)
    - `datumErsteVeroeffentlichung`: string (`YYYY-MM-DD`)
    - `stellenlokationen`: `[ { adresse: { plz, ort, region, land } } ]`
    - `arbeitszeitVollzeit`: boolean

### 2. Job Detail

- **Path:** `/pc/v4/jobdetails/{encryptedJobCode}`
- **Method:** `GET`
- **Path Parameter:**
  - `encryptedJobCode`: Base64-encoded string of the `referenznummer`, e.g. `btoa("12265-350002_JB5242033-S")`
- **Response Structure:**
  - `stellenangebotsBeschreibung`: Full text / HTML description of the role
  - `arbeitszeitVollzeit`: boolean
  - `vertragsdauer`: string
  - `eintrittszeitraum`: `{ von: "..." }`
  - `verguetungsangabe`: string
  - `gehaltsspanneVon`: float
  - `gehaltsspanneBis`: float
  - `stellenlokationen`: array
