import { describe, expect, it, vi } from "vitest"
import { apiFetch } from "@/lib/api"

function stubFetch(status: number, body: unknown) {
  const fetchMock = vi.fn(
    async (_url: string, _init?: RequestInit) =>
      new Response(body === null ? null : JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
      }),
  )
  vi.stubGlobal("fetch", fetchMock)
  return fetchMock
}

describe("apiFetch", () => {
  it("calls /api and returns the JSON body", async () => {
    const fetchMock = stubFetch(200, { status: "ok" })

    await expect(apiFetch("/health")).resolves.toEqual({ status: "ok" })
    expect(fetchMock).toHaveBeenCalledWith("/api/health", expect.objectContaining({ method: "GET" }))
  })

  it("throws an ApiError with the server's message", async () => {
    stubFetch(401, { detail: "Wrong email or password." })

    await expect(apiFetch("/auth/login", { method: "POST", body: {} })).rejects.toMatchObject({
      name: "ApiError",
      status: 401,
      message: "Wrong email or password.",
    })
  })

  it("returns null when the response has no body", async () => {
    stubFetch(204, null)

    await expect(apiFetch("/auth/logout", { method: "POST" })).resolves.toBeNull()
  })

  it("sends FormData as-is so the browser can set the upload headers", async () => {
    const fetchMock = stubFetch(201, { id: "d1" })
    const form = new FormData()
    form.append("file", new File(["hello"], "notes.md"))

    await apiFetch("/documents", { method: "POST", body: form })

    const init = fetchMock.mock.calls[0][1]
    expect(init?.body).toBe(form)
    expect(init?.headers).toBeUndefined()
  })
})
