import { BASE_URL, fetchWithBackoff, type JobCard } from "../helpers.js"

export interface SearchOpts {
  query?: string
  location?: string
  page?: number
  limit?: number
  jobage?: number
  format?: "json" | "table" | "plain"
}

interface RawAddress {
  plz?: string
  ort?: string
  region?: string
  land?: string
}

interface RawLocation {
  adresse?: RawAddress
}

interface RawJob {
  referenznummer?: string
  stellenangebotsTitel?: string
  firma?: string
  stellenlokationen?: RawLocation[]
  datumErsteVeroeffentlichung?: string
  aenderungsdatum?: string
}

interface SearchResponse {
  maxErgebnisse?: number
  page?: number
  size?: number
  ergebnisliste?: RawJob[]
}

export async function runSearch(opts: SearchOpts): Promise<void> {
  const query = opts.query || ""
  const location = opts.location || "Deutschland"
  const page = opts.page || 1
  const limit = opts.limit || 20
  const jobage = opts.jobage

  const params = new URLSearchParams()
  if (query) params.set("was", query)
  if (location) params.set("wo", location)
  params.set("page", String(page))
  params.set("size", String(Math.min(limit * 3, 50))) // fetch extra to account for client-side jobage filter

  if (jobage !== undefined) {
    if (jobage === 0) params.set("veroeffentlichtseit", "0")
    else if (jobage <= 2) params.set("veroeffentlichtseit", "7") // broad fetch; exact cutoff below
    else if (jobage <= 7) params.set("veroeffentlichtseit", "7")
    else if (jobage <= 14) params.set("veroeffentlichtseit", "14")
    else if (jobage <= 28) params.set("veroeffentlichtseit", "28")
  }

  let data: SearchResponse | null = null
  let pagesFetched = 0
  let exhausted = false
  const seenIds = new Set<string>()
  const today = new Date()
  const todayDate = new Date(today.getFullYear(), today.getMonth(), today.getDate())

  const results: JobCard[] = []
  for (let currentPage = page; currentPage < page + 10; currentPage++) {
    params.set("page", String(currentPage))
    data = await fetchWithBackoff<SearchResponse>(`${BASE_URL}/pc/v6/jobs?${params.toString()}`)
    pagesFetched++
    const items = data?.ergebnisliste || []
    if (!items.length) { exhausted = true; break }
    let newIds = 0
    for (const raw of items) {
    if (!raw.referenznummer || seenIds.has(raw.referenznummer)) continue
    seenIds.add(raw.referenznummer)
    newIds++
    if (!raw.referenznummer || !raw.stellenangebotsTitel || !raw.firma) continue

    const pubDate = raw.datumErsteVeroeffentlichung || null

    if (jobage !== undefined && pubDate) {
      const pParts = pubDate.split("T")[0].split("-").map(Number)
      if (pParts.length === 3 && !isNaN(pParts[0])) {
        const pDate = new Date(pParts[0], pParts[1] - 1, pParts[2])
        const diffDays = Math.floor((todayDate.getTime() - pDate.getTime()) / (1000 * 60 * 60 * 24))
        if (diffDays > jobage || diffDays < 0) {
          continue
        }
      }
    } else if (jobage !== undefined && !pubDate) {
      continue
    }

    const locObj = raw.stellenlokationen?.[0]?.adresse
    const locParts = [locObj?.ort, locObj?.land].filter(Boolean)
    const locStr = locParts.length > 0 ? locParts.join(", ") : "Deutschland"

    results.push({
      id: raw.referenznummer,
      title: raw.stellenangebotsTitel.trim(),
      company: raw.firma.trim(),
      location: locStr,
      date: pubDate,
      url: `https://www.arbeitsagentur.de/jobsuche/jobdetail/${raw.referenznummer}`,
    })

    if (results.length >= limit) break
  }

    if (results.length >= limit) break
    if (newIds === 0) break
    if (items.length < Number(params.get("size"))) { exhausted = true; break }
  }

  const format = opts.format || "json"
  if (format === "json") {
    const payload = {
      meta: {
        count: results.length,
        total: data?.maxErgebnisse || results.length,
        page,
        pagesFetched,
        truncated: !exhausted,
      },
      results,
    }
    process.stdout.write(JSON.stringify(payload, null, 2) + "\n")
  } else if (format === "table") {
    console.table(
      results.map((r) => ({
        ID: r.id,
        Title: r.title.slice(0, 40),
        Company: r.company.slice(0, 30),
        Location: r.location?.slice(0, 20) || "-",
        Date: r.date || "-",
      }))
    )
  } else {
    for (const r of results) {
      console.log(`[${r.id}] ${r.title} — ${r.company} (${r.location || "-"}) | ${r.date || "-"}`)
      console.log(`  ${r.url}`)
    }
  }
}
