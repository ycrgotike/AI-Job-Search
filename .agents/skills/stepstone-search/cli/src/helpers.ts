export const BASE_URL = "https://www.stepstone.de"
export const UA = "Mozilla/5.0 (compatible; stepstone-cli/1.0)"

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

export async function fetchHtml(url: string): Promise<string> {
  const maxRetries = 4
  let delay = 500
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const res = await fetch(url, {
        headers: {
          "User-Agent": UA,
          Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
          "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        },
        signal: AbortSignal.timeout(15000),
      })
      if (res.status === 429 || res.status >= 500) {
        if (attempt === maxRetries) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`)
        }
        await new Promise((r) => setTimeout(r, delay))
        delay = Math.min(delay * 2, 4000)
        continue
      }
      if (res.status === 404) return ""
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`)
      }
      return await res.text()
    } catch (err: any) {
      if (attempt === maxRetries) throw err
      await new Promise((r) => setTimeout(r, delay))
      delay = Math.min(delay * 2, 4000)
    }
  }
  return ""
}

export function stripHtml(raw: string): string {
  if (!raw) return ""
  return raw
    .replace(/<[^>]+>/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, " ")
    .trim()
}

export function extractJsonLd(html: string): any | null {
  const matches = html.matchAll(/<script[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi)
  for (const m of matches) {
    try {
      const parsed = JSON.parse(m[1])
      if (parsed["@type"] === "JobPosting") return parsed
      if (Array.isArray(parsed["@graph"])) {
        const job = parsed["@graph"].find((item: any) => item["@type"] === "JobPosting")
        if (job) return job
      }
    } catch {}
  }
  return null
}

export interface JobCard {
  id: string
  title: string
  company: string | null
  location: string | null
  date: string | null
  url: string
  description?: string
}

export interface JobDetail extends JobCard {
  description: string
  validThrough?: string | null
  employmentType?: string | null
}
