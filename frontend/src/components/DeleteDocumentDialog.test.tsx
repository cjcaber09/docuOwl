import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { DeleteDocumentDialog } from "@/components/DeleteDocumentDialog"

describe("DeleteDocumentDialog", () => {
  it("does nothing when the user cancels", async () => {
    const onConfirm = vi.fn()
    render(<DeleteDocumentDialog filename="Q3.pdf" onConfirm={onConfirm} />)

    fireEvent.click(screen.getByRole("button", { name: "Delete Q3.pdf" }))
    fireEvent.click(await screen.findByRole("button", { name: "Cancel" }))

    expect(onConfirm).not.toHaveBeenCalled()
  })

  it("deletes after the user confirms", async () => {
    const onConfirm = vi.fn()
    render(<DeleteDocumentDialog filename="Q3.pdf" onConfirm={onConfirm} />)

    fireEvent.click(screen.getByRole("button", { name: "Delete Q3.pdf" }))
    fireEvent.click(await screen.findByRole("button", { name: "Delete" }))

    expect(onConfirm).toHaveBeenCalledOnce()
  })
})
