import { create } from "zustand"
import type { Citation } from "@/lib/apiTypes"

// The answer being written right now. Saved messages live in TanStack Query, never here.
export type StreamingAnswer = {
  conversationId: string
  question: string
  text: string
  citations: Citation[]
  error: string | null
}

type AnswerState = {
  answer: StreamingAnswer | null
  start: (conversationId: string, question: string) => void
  addText: (text: string) => void
  addCitation: (citation: Citation) => void
  fail: (message: string) => void
  clear: () => void
}

export const useAnswerStore = create<AnswerState>()((set) => ({
  answer: null,
  start: (conversationId, question) => set({ answer: { conversationId, question, text: "", citations: [], error: null } }),
  addText: (text) => set((state) => (state.answer ? { answer: { ...state.answer, text: state.answer.text + text } } : state)),
  addCitation: (citation) =>
    set((state) => (state.answer ? { answer: { ...state.answer, citations: [...state.answer.citations, citation] } } : state)),
  fail: (message) => set((state) => (state.answer ? { answer: { ...state.answer, error: message } } : state)),
  clear: () => set({ answer: null }),
}))
