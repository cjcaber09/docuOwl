import { QueryClientProvider } from "@tanstack/react-query"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { createMemoryRouter, RouterProvider } from "react-router"
import { describe, expect, it, vi } from "vitest"
import { createQueryClient } from "@/lib/queryClient"
import { ChatPage } from "@/pages/ChatPage"
import { useAnswerStore } from "@/stores/answerStore"

const CONVERSATION = {
  id: "c1",
  title: "Refund policy",
  messages: [{ id: "m1", role: "user", content: "Earlier question", citations: [], createdAt: "2026-11-20T00:00:00Z" }],
}

function stubFetch(status: number, body: unknown) {
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(body), { status })))
}

describe("ChatPage", () => {
  it("keeps the conversation and offers Retry when the server can't be reached", async () => {
    useAnswerStore.getState().clear()
    stubFetch(200, CONVERSATION)
    const router = createMemoryRouter([{ path: "/chat/:conversationId", element: <ChatPage /> }], {
      initialEntries: ["/chat/c1"],
    })
    render(
      <QueryClientProvider client={createQueryClient()}>
        <RouterProvider router={router} />
      </QueryClientProvider>,
    )
    expect(await screen.findByText("Earlier question")).toBeInTheDocument()

    // The server goes away: the question fails, and so does the refresh after it.
    stubFetch(500, {})
    fireEvent.change(screen.getByLabelText("Your question"), { target: { value: "New question" } })
    fireEvent.click(screen.getByRole("button", { name: "Send question" }))

    // Wait for both failed requests: sending the question, then reloading the conversation.
    await waitFor(() => expect(vi.mocked(fetch).mock.calls.length).toBeGreaterThanOrEqual(2))
    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument()
    expect(screen.getByText("Earlier question")).toBeInTheDocument()
  })
})
