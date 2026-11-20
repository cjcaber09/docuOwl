import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { CitationChip } from "@/components/CitationChip"

describe("CitationChip", () => {
  it("labels a citation of a deleted file", () => {
    render(
      <CitationChip
        citation={{ filename: "Old-pricing.docx", location: "Annual billing", quote: "Pro rata.", deleted: true }}
      />,
    )

    expect(screen.getByRole("button", { name: "Old-pricing.docx (deleted) · Annual billing" })).toBeInTheDocument()
  })
})
