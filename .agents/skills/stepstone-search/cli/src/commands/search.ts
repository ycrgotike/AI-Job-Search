import { BASE_URL, fetchHtml, type JobCard } from "../helpers.js"
import { fetchStepstoneDetail } from "./detail.js"

export interface SearchOpts {
  query?: string
  location?: string
  page?: number
  limit?: number
  jobage?: number
  format?: "json" | "table" | "plain"
}

export async function runSearch(opts: SearchOpts): Promise<void> {
  const query = opts.query || "Data"
  const location = opts.location || "Deutschland"
  const page = opts.page || 1
  const limit = opts.limit || 20
  const jobage = opts.jobage

  const qSlug = query
    .toLowerCase()
    .trim()
    .replace(/[ä]/g, "ae")
    .replace(/[ö]/g, "oe")
    .replace(/[ü]/g, "ue")
    .replace(/[ß]/g, "ss")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")

  const locSlug = location
    .toLowerCase()
    .trim()
    .replace(/[ä]/g, "ae")
    .replace(/[ö]/g, "oe")
    .replace(/[ü]/g, "ue")
    .replace(/[ß]/g, "ss")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")

  let searchUrl = `${BASE_URL}/jobs/${qSlug}/in-${locSlug}`
  const params = new URLSearchParams()
  if (page > 1) params.set("page", String(page))
  if (jobage !== undefined) {
    if (jobage <= 1) params.set("ag", "age_1")
    else if (jobage <= 7) params.set("ag", "age_7")
  }

  const qs = params.toString()
  if (qs) searchUrl += `?${qs}`

  const html = await fetchHtml(searchUrl)
  const matches = [...html.matchAll(/href="(\/stellenangebote--[^"]+--(\d+)-inline\.html)"/g)]
  const seenPaths = new Set<string>()
  const candidateUrls: string[] = []

  for (const m of matches) {
    const path = m[1]
    if (!seenPaths.has(path)) {
      seenPaths.add(path)
      candidateUrls.push(`${BASE_URL}${path}`)
      if (candidateUrls.length >= Math.max(limit * 2, 10)) break
    }
  }

  // Concurrently fetch details for candidate cards to obtain verified datePosted & company
  const details = await Promise.all(
    candidateUrls.map(async (u) => {
      try {
        return await fetchStepstoneDetail(u)
      } catch {
        return null
      }
    })
  )

  const today = new Date()
  const results: JobCard[] = []

  for (const item of details) {
    if (!item || !item.title) continue

    if (jobage !== undefined) {
      if (!item.date) continue
      const pDate = new Date(item.date)
      const diffDays = (today.getTime() - pDate.getTime()) / (1000 * 60 * 60 * 24)
      if (diffDays > jobage || diffDays < 0) {
        continue
      }
    }

    results.push({
      id: item.id,
      title: item.title,
      company: item.company,
      location: item.location,
      date: item.date,
      url: item.url,
      description: item.description,
    })

    if (results.length >= limit) break
  }

  const format = opts.format || "json"
  if (format === "json") {
    const payload = {
      meta: {
        count: results.length,
        page,
      },
      results,
    }
    process.stdout.write(JSON.stringify(payload, null, 2) + "\n")
  } else if (format === "table") {
    console.table(
      results.map((r) => ({
        ID: r.id,
        Title: r.title.slice(0, 40),
        Company: r.company?.slice(0, 30) || "-",
        Location: r.location?.slice(0, 20) || "-",
        Date: r.date || "-",
      }))
    )
  } else {
    for (const r of results) {
      console.log(`[${r.id}] ${r.title} — ${r.company || "-"} (${r.location || "-"}) | ${r.date || "-"}`)
      console.log(`  ${r.url}`)
    }
  }
}
