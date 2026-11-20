import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { ConfirmDeleteDialog } from "@/components/ConfirmDeleteDialog"

describe("ConfirmDeleteDialog", () => {
  it("does nothing when the user cancels", async () => {
    const onConfirm = vi.fn()
    render(<ConfirmDeleteDialog itemName="Q3.pdf" description="Owl will forget everything in this file." onConfirm={onConfirm} />)

    fireEvent.click(screen.getByRole("button", { name: "Delete Q3.pdf" }))
    fireEvent.click(await screen.findByRole("button", { name: "Cancel" }))

    expect(onConfirm).not.toHaveBeenCalled()
  })

  it("deletes after the user confirms", async () => {
    const onConfirm = vi.fn()
    render(<ConfirmDeleteDialog itemName="Q3.pdf" description="Owl will forget everything in this file." onConfirm={onConfirm} />)

    fireEvent.click(screen.getByRole("button", { name: "Delete Q3.pdf" }))
    fireEvent.click(await screen.findByRole("button", { name: "Delete" }))

    expect(onConfirm).toHaveBeenCalledOnce()
  })
})
