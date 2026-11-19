export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

type RequestOptions = {
  method?: string
  body?: unknown
}

function parseJson(text: string): unknown {
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

function errorMessage(data: unknown, status: number): string {
  if (typeof data === "object" && data !== null && "detail" in data && typeof data.detail === "string") {
    return data.detail
  }
  if (status === 422) return "Please check the form and try again."
  return "Something went wrong. Please try again."
}

function requestBody(body: unknown): { body?: BodyInit; headers?: HeadersInit } {
  if (body === undefined) return {}
  // For files, the browser writes the multipart Content-Type (with its boundary) itself.
  if (body instanceof FormData) return { body }
  return { body: JSON.stringify(body), headers: { "Content-Type": "application/json" } }
}

/** Calls Owl's backend. `path` is relative to /api, e.g. "/auth/me". */
export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method: options.method ?? "GET",
    credentials: "same-origin",
    ...requestBody(options.body),
  })
  const text = await response.text()
  const data = text ? parseJson(text) : null
  if (!response.ok) throw new ApiError(response.status, errorMessage(data, response.status))
  return data as T
}
