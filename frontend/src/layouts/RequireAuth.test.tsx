import { QueryClientProvider } from "@tanstack/react-query"
import { render, screen } from "@testing-library/react"
import { createMemoryRouter, RouterProvider } from "react-router"
import { describe, expect, it, vi } from "vitest"
import { RequireAuth } from "@/layouts/RequireAuth"
import { createQueryClient } from "@/lib/queryClient"

function stubCurrentUser(status: number, body: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } })),
  )
}

function renderAt(path: string) {
  const router = createMemoryRouter(
    [
      { element: <RequireAuth />, children: [{ path: "/chat", element: <p>Private chat</p> }] },
      { path: "/login", element: <p>Login page</p> },
    ],
    { initialEntries: [path] },
  )
  render(
    <QueryClientProvider client={createQueryClient()}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
}

describe("RequireAuth", () => {
  it("sends logged-out visitors to the login page", async () => {
    stubCurrentUser(401, { detail: "Please log in." })

    renderAt("/chat")

    expect(await screen.findByText("Login page")).toBeInTheDocument()
  })

  it("shows the page to logged-in users", async () => {
    stubCurrentUser(200, { id: "u1", email: "reader@example.com" })

    renderAt("/chat")

    expect(await screen.findByText("Private chat")).toBeInTheDocument()
  })
})
