import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { StatusBadge } from "@/components/StatusBadge"

describe("StatusBadge", () => {
  it.each([
    ["processing", "Processing"],
    ["ready", "Ready"],
    ["failed", "Failed"],
  ] as const)("shows %s as %s", (status, label) => {
    render(<StatusBadge status={status} />)

    expect(screen.getByText(label)).toBeInTheDocument()
  })
})
