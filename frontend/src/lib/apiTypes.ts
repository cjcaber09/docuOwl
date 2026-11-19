// The shapes the backend sends back. Keep in sync with backend/app/auth/schemas.py and /api/config.

export type User = {
  id: string
  email: string
}

export type AppConfig = {
  storageEnabled: boolean
  emailEnabled: boolean
}

export type DocumentStatus = "processing" | "ready" | "failed"

// Named OwlDocument so it never gets mixed up with the browser's built-in `Document`.
export type OwlDocument = {
  id: string
  filename: string
  fileType: string
  status: DocumentStatus
  failureReason: string | null
  pageCount: number | null
  createdAt: string
}
