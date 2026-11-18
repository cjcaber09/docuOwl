// ALL sample content for the UI lives here.
// It is deleted page by page when the real backend is connected (build steps 5–7).

export type DocumentStatus = "processing" | "ready" | "failed"

export type SampleDocument = {
  id: string
  filename: string
  fileType: "pdf" | "docx" | "txt" | "md"
  status: DocumentStatus
  failureReason: string | null
  pageCount: number | null
  uploadedAt: string
}

export type SampleCitation = {
  id: string
  filename: string
  location: string
  quote: string
  deleted: boolean
}

export type SampleMessage = {
  id: string
  role: "user" | "assistant"
  content: string
  citations: SampleCitation[]
}

export type SampleConversation = {
  id: string
  title: string
  updatedAt: string
  messages: SampleMessage[]
}

export const sampleConfig = {
  storageEnabled: true,
  emailEnabled: true,
}

export const sampleUser = {
  email: "you@example.com",
}

export const sampleDocuments: SampleDocument[] = [
  {
    id: "doc-1",
    filename: "Terms-of-Service.pdf",
    fileType: "pdf",
    status: "ready",
    failureReason: null,
    pageCount: 12,
    uploadedAt: "2026-11-12T09:30:00Z",
  },
  {
    id: "doc-2",
    filename: "Q3-report.pdf",
    fileType: "pdf",
    status: "processing",
    failureReason: null,
    pageCount: null,
    uploadedAt: "2026-11-19T08:05:00Z",
  },
  {
    id: "doc-3",
    filename: "Support-notes.md",
    fileType: "md",
    status: "ready",
    failureReason: null,
    pageCount: null,
    uploadedAt: "2026-11-10T14:12:00Z",
  },
  {
    id: "doc-4",
    filename: "Scanned-invoice.pdf",
    fileType: "pdf",
    status: "failed",
    failureReason: "No text found, scanned PDFs aren't supported yet.",
    pageCount: null,
    uploadedAt: "2026-11-18T17:44:00Z",
  },
  {
    id: "doc-5",
    filename: "Team-handbook.docx",
    fileType: "docx",
    status: "ready",
    failureReason: null,
    pageCount: null,
    uploadedAt: "2026-11-02T11:00:00Z",
  },
]

export const sampleConversations: SampleConversation[] = [
  {
    id: "conv-1",
    title: "Refund policy for the Pro plan",
    updatedAt: "2026-11-19T10:20:00Z",
    messages: [
      {
        id: "msg-1",
        role: "user",
        content: "What's the refund policy for the Pro plan?",
        citations: [],
      },
      {
        id: "msg-2",
        role: "assistant",
        content:
          "Pro plan purchases can be refunded within 30 days of payment. After 30 days, refunds are only given if the service was unavailable for more than 72 hours in a billing month.",
        citations: [
          {
            id: "cit-1",
            filename: "Terms-of-Service.pdf",
            location: "p. 4",
            quote: "Purchases of the Pro plan are eligible for a full refund within thirty (30) days of payment.",
            deleted: false,
          },
          {
            id: "cit-2",
            filename: "Support-notes.md",
            location: "Refunds",
            quote: "After 30 days we only refund if downtime exceeded 72 hours in the billing month.",
            deleted: false,
          },
        ],
      },
      {
        id: "msg-3",
        role: "user",
        content: "And for annual plans?",
        citations: [],
      },
      {
        id: "msg-4",
        role: "assistant",
        content:
          "Annual plans have the same 30-day full refund window. After that, unused full months are refunded pro rata.",
        citations: [
          {
            id: "cit-3",
            filename: "Terms-of-Service.pdf",
            location: "p. 5",
            quote: "Annual subscriptions cancelled after thirty (30) days receive a pro-rata refund of unused full months.",
            deleted: false,
          },
          {
            id: "cit-4",
            filename: "Old-pricing.docx",
            location: "Annual billing",
            quote: "Annual billing is refundable on a pro-rata basis.",
            deleted: true,
          },
        ],
      },
    ],
  },
  {
    id: "conv-2",
    title: "Q3 revenue summary",
    updatedAt: "2026-11-18T16:00:00Z",
    messages: [
      {
        id: "msg-5",
        role: "user",
        content: "Summarize Q3 revenue.",
        citations: [],
      },
      {
        id: "msg-6",
        role: "assistant",
        content: "I couldn't find that in your documents. Q3-report.pdf is still being processed, so try again once it's ready.",
        citations: [],
      },
    ],
  },
  {
    id: "conv-3",
    title: "Onboarding checklist",
    updatedAt: "2026-11-15T09:00:00Z",
    messages: [
      {
        id: "msg-7",
        role: "user",
        content: "What should a new hire do in their first week?",
        citations: [],
      },
      {
        id: "msg-8",
        role: "assistant",
        content: "In the first week a new hire sets up their accounts, meets their buddy, and reads the security policy.",
        citations: [
          {
            id: "cit-5",
            filename: "Team-handbook.docx",
            location: "First week",
            quote: "Week one: set up accounts, meet your onboarding buddy, read the security policy.",
            deleted: false,
          },
        ],
      },
    ],
  },
]
