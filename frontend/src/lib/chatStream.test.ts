import { describe, expect, it, vi } from "vitest"
import type { AnswerEvent } from "@/lib/apiTypes"
import { streamAnswer } from "@/lib/chatStream"

/** A fake fetch whose body arrives in the given pieces, like a slow network would deliver it. */
function stubStreamingFetch(status: number, pieces: string[]) {
  const encoder = new TextEncoder()
  let next = 0
  const reader = {
    read: async () =>
      next < pieces.length ? { value: encoder.encode(pieces[next++]), done: false } : { value: undefined, done: true },
  }
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({ ok: status < 400, status, body: { getReader: () => reader }, text: async () => pieces.join("") })),
  )
}

async function collect(conversationId: string) {
  const received: AnswerEvent[] = []
  await streamAnswer(conversationId, "Refunds?", (event) => received.push(event))
  return received
}

describe("streamAnswer", () => {
  it("joins a line that arrives in two pieces", async () => {
    stubStreamingFetch(200, ['{"type":"text","text":"Hel', 'lo"}\n{"type":"done","message":null,"title":null}\n'])

    expect(await collect("c1")).toEqual([
      { type: "text", text: "Hello" },
      { type: "done", message: null, title: null },
    ])
  })

  it("reads a last line without a line break", async () => {
    stubStreamingFetch(200, ['{"type":"error","message":"Owl is having trouble right now, please try again."}'])

    expect(await collect("c1")).toEqual([
      { type: "error", message: "Owl is having trouble right now, please try again." },
    ])
  })

  it("turns an error answer into an ApiError with the server's message", async () => {
    stubStreamingFetch(429, ['{"detail":"You\'ve asked 100 questions today. The limit resets at midnight UTC."}'])

    await expect(collect("c1")).rejects.toMatchObject({
      name: "ApiError",
      status: 429,
      message: "You've asked 100 questions today. The limit resets at midnight UTC.",
    })
  })
})
