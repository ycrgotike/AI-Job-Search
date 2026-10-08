export const BASE_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service"
export const API_KEY = "jobboerse-jobsuche"
export const UA = "Mozilla/5.0 (compatible; arbeitsagentur-cli/1.0)"

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

export async function fetchWithBackoff<T>(url: string): Promise<T | null> {
  const maxRetries = 4
  let delay = 500
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const res = await fetch(url, {
        headers: {
          "X-API-Key": API_KEY,
          "User-Agent": UA,
          Accept: "application/json",
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
      if (res.status === 404) return null
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`)
      }
      return (await res.json()) as T
    } catch (err: any) {
      if (attempt === maxRetries) throw err
      await new Promise((r) => setTimeout(r, delay))
      delay = Math.min(delay * 2, 4000)
    }
  }
  return null
}

export interface JobCard {
  id: string
  title: string
  company: string
  location: string | null
  date: string | null
  url: string
}

export interface JobDetail extends JobCard {
  externalUrls?: string[]
  description: string
  employmentType?: string
  salary?: string
}
