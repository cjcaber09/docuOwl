import { describe, expect, it, vi } from "vitest"
import { apiFetch } from "@/lib/api"

function stubFetch(status: number, body: unknown) {
  const fetchMock = vi.fn(
    async () =>
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
})
