#!/usr/bin/env bun
import { runSearch } from "./commands/search.js"
import { runDetail } from "./commands/detail.js"
import { writeError } from "./helpers.js"

const argv = process.argv.slice(2)
const command = argv[0]

function printHelp(): void {
  console.log(`
stepstone-cli — Search job postings from StepStone Germany

Commands:
  search [flags]           Search job postings
  detail <url|id>          Fetch job detail and full description

Search Flags:
  -q, --query <text>       Keywords or job title (default: Data)
  -l, --location <text>    City, region, or 'Deutschland' (default: Deutschland)
  --jobage <days>          Max posting age in days (e.g. 1, 2, 7)
  --page <n>               Page number (1-indexed, default 1)
  -n, --limit <n>          Result limit (default 20)
  --format <type>          Output format: json (default), table, plain

Detail Flags:
  --format <type>          Output format: json (default), plain

Examples:
  bun run src/cli.ts search -q "Data Engineer" -l "Deutschland" --jobage 2 --format table
  bun run src/cli.ts detail "https://www.stepstone.de/stellenangebote--...--14434297-inline.html" --format plain
`)
}

if (!command || command === "-h" || command === "--help" || command === "help") {
  printHelp()
  process.exit(0)
}

function parseFlags(args: string[]): Record<string, any> {
  const flags: Record<string, any> = { _: [] }
  for (let i = 0; i < args.length; i++) {
    const a = args[i]
    if (a.startsWith("--")) {
      const key = a.slice(2)
      if (i + 1 < args.length && !args[i + 1].startsWith("-")) {
        flags[key] = args[++i]
      } else {
        flags[key] = true
      }
    } else if (a.startsWith("-")) {
      const key = a.slice(1)
      const mapped = key === "q" ? "query" : key === "l" ? "location" : key === "n" ? "limit" : key
      if (i + 1 < args.length && !args[i + 1].startsWith("-")) {
        flags[mapped] = args[++i]
      } else {
        flags[mapped] = true
      }
    } else {
      flags._.push(a)
    }
  }
  return flags
}

const flags = parseFlags(argv.slice(1))

try {
  if (command === "search") {
    await runSearch({
      query: flags.query,
      location: flags.location,
      page: flags.page ? parseInt(flags.page, 10) : 1,
      limit: flags.limit ? parseInt(flags.limit, 10) : 20,
      jobage: flags.jobage !== undefined ? parseInt(flags.jobage, 10) : undefined,
      format: flags.format || "json",
    })
  } else if (command === "detail") {
    const target = flags._[0] || flags.id || flags.url
    if (!target) {
      writeError("Missing job URL or ID", "MISSING_ARG")
      process.exit(1)
    }
    await runDetail({
      urlOrId: target,
      format: flags.format || "json",
    })
  } else {
    writeError(`Unknown command: ${command}`, "UNKNOWN_COMMAND")
    printHelp()
    process.exit(1)
  }
} catch (err: any) {
  writeError(err.message || String(err), "RUNTIME_ERROR")
  process.exit(1)
}
