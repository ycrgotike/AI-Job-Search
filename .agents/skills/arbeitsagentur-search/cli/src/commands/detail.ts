import { BASE_URL, fetchWithBackoff, writeError, type JobDetail } from "../helpers.js"

export interface DetailOpts {
  idOrUrl: string
  format?: "json" | "plain"
}

interface RawDetailResponse {
  [key: string]: unknown
  stellenangebotsTitel?: string
  firma?: string
  stellenangebotsBeschreibung?: string
  arbeitszeitVollzeit?: boolean
  vertragsdauer?: string
  datumErsteVeroeffentlichung?: string
  aenderungsdatum?: string
  gehaltsspanneVon?: number
  gehaltsspanneBis?: number
  verguetungsangabe?: string
  stellenlokationen?: Array<{
    adresse?: {
      ort?: string
      land?: string
    }
  }>
  referenznummer?: string
}

// Preserve explicit URL/link fields from the portal, including nested referral metadata.
export function externalJobUrls(value: unknown): string[] {
  const found = new Set<string>()
  function visit(node: unknown, key = ""): void {
    if (typeof node === "string" && /url|link/i.test(key) && /^https?:\/\//i.test(node)) {
      found.add(node)
    } else if (Array.isArray(node)) {
      for (const item of node) visit(item, key)
    } else if (node && typeof node === "object") {
      for (const [name, item] of Object.entries(node)) visit(item, name)
    }
  }
  visit(value)
  return [...found]
}

export async function runDetail(opts: DetailOpts): Promise<void> {
  let refnr = opts.idOrUrl.trim()
  if (refnr.includes("/")) {
    const parts = refnr.split("/").filter(Boolean)
    refnr = parts[parts.length - 1]
  }

  if (!refnr) {
    writeError("Missing job referenznummer or URL", "INVALID_ARG")
    process.exit(1)
  }

  const encoded = Buffer.from(refnr).toString("base64")
  const url = `${BASE_URL}/pc/v4/jobdetails/${encoded}`

  const data = await fetchWithBackoff<RawDetailResponse>(url)
  if (!data) {
    writeError(`Job posting not found for ${refnr}`, "NOT_FOUND")
    process.exit(1)
  }

  const locObj = data.stellenlokationen?.[0]?.adresse
  const locStr = [locObj?.ort, locObj?.land].filter(Boolean).join(", ") || "Deutschland"

  let salaryStr: string | undefined = undefined
  if (data.gehaltsspanneVon || data.gehaltsspanneBis) {
    salaryStr = `${data.gehaltsspanneVon || 0} - ${data.gehaltsspanneBis || 0} EUR (${data.verguetungsangabe || ""})`
  }

  const result: JobDetail = {
    id: data.referenznummer || refnr,
    title: (data.stellenangebotsTitel || "").trim(),
    company: (data.firma || "").trim(),
    location: locStr,
    date: data.datumErsteVeroeffentlichung || data.aenderungsdatum?.split("T")[0] || null,
    url: `https://www.arbeitsagentur.de/jobsuche/jobdetail/${refnr}`,
    description: (data.stellenangebotsBeschreibung || "").trim(),
    employmentType: data.arbeitszeitVollzeit ? "Vollzeit" : "Teilzeit",
    salary: salaryStr,
    externalUrls: externalJobUrls(data),
  }

  const format = opts.format || "json"
  if (format === "json") {
    process.stdout.write(JSON.stringify(result, null, 2) + "\n")
  } else {
    console.log(`Title:       ${result.title}`)
    console.log(`Company:     ${result.company}`)
    console.log(`Location:    ${result.location}`)
    console.log(`Date:        ${result.date || "N/A"}`)
    console.log(`URL:         ${result.url}`)
    if (result.salary) console.log(`Salary:      ${result.salary}`)
    console.log("\n--- Description ---")
    console.log(result.description)
  }
}
