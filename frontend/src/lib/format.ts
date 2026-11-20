import type { Citation } from "@/lib/apiTypes"

export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(iso))
}

export function citationLabel(citation: Citation): string {
  return `${citation.filename}${citation.deleted ? " (deleted)" : ""} · ${citation.location}`
}
