import { BASE_URL, fetchHtml, extractJsonLd, stripHtml, writeError, type JobDetail } from "../helpers.js"

export interface DetailOpts {
  urlOrId: string
  format?: "json" | "plain"
}

export async function fetchStepstoneDetail(urlOrId: string): Promise<JobDetail | null> {
  let targetUrl = urlOrId.trim()
  if (!targetUrl.startsWith("http")) {
    // If just an ID or path was passed
    if (targetUrl.startsWith("/")) {
      targetUrl = `${BASE_URL}${targetUrl}`
    } else {
      targetUrl = `${BASE_URL}/stellenangebote--job--${targetUrl}-inline.html`
    }
  }

  const html = await fetchHtml(targetUrl)
  if (!html) return null

  const schema = extractJsonLd(html)
  if (!schema) {
    // Fallback: extract title tag
    const titleMatch = html.match(/<title>([^<]+)<\/title>/i)
    return {
      id: targetUrl.match(/--(\d+)-inline/)?.[1] || targetUrl,
      title: titleMatch ? titleMatch[1].split("|")[0].trim() : "Job Posting",
      company: null,
      location: null,
      date: null,
      url: targetUrl,
      description: stripHtml(html).slice(0, 2000),
    }
  }

  const jobLocation = schema.jobLocation
  let locStr: string | null = null
  if (Array.isArray(jobLocation) && jobLocation.length > 0) {
    const addr = jobLocation[0]?.address
    locStr = [addr?.addressLocality, addr?.addressRegion, addr?.addressCountry].filter(Boolean).join(", ")
  } else if (jobLocation?.address) {
    const addr = jobLocation.address
    locStr = [addr?.addressLocality, addr?.addressRegion, addr?.addressCountry].filter(Boolean).join(", ")
  }

  const rawDate = schema.datePosted ? schema.datePosted.split("T")[0] : null

  return {
    id: targetUrl.match(/--(\d+)-inline/)?.[1] || schema.identifier?.value || targetUrl,
    title: schema.title || "",
    company: schema.hiringOrganization?.name || null,
    location: locStr,
    date: rawDate,
    url: schema.url || targetUrl,
    description: stripHtml(schema.description || ""),
    validThrough: schema.validThrough ? schema.validThrough.split("T")[0] : null,
    employmentType: schema.employmentType || null,
  }
}

export async function runDetail(opts: DetailOpts): Promise<void> {
  const detail = await fetchStepstoneDetail(opts.urlOrId)
  if (!detail) {
    writeError(`Job detail not found for ${opts.urlOrId}`, "NOT_FOUND")
    process.exit(1)
  }

  const format = opts.format || "json"
  if (format === "json") {
    process.stdout.write(JSON.stringify(detail, null, 2) + "\n")
  } else {
    console.log(`Title:       ${detail.title}`)
    console.log(`Company:     ${detail.company || "N/A"}`)
    console.log(`Location:    ${detail.location || "N/A"}`)
    console.log(`Date:        ${detail.date || "N/A"}`)
    console.log(`URL:         ${detail.url}`)
    if (detail.validThrough) console.log(`Deadline:    ${detail.validThrough}`)
    if (detail.employmentType) console.log(`Type:        ${detail.employmentType}`)
    console.log("\n--- Description ---")
    console.log(detail.description)
  }
}
