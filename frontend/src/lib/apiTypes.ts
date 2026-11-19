// The shapes the backend sends back. Keep in sync with backend/app/auth/schemas.py and /api/config.

export type User = {
  id: string
  email: string
}

export type AppConfig = {
  storageEnabled: boolean
  emailEnabled: boolean
}
