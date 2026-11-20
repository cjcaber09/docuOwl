import { expect, test } from "@playwright/test"

const NOTES = "# Refunds\nPro plans can be refunded within 30 days of payment.\n\n# Annual plans\nUnused full months are refunded pro rata.\n"

test("sign up, upload a file, ask, and get a cited answer", async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`

  await page.goto("/signup")
  await page.getByLabel("Email").fill(email)
  await page.getByLabel("Password", { exact: true }).fill("e2e password 123")
  await page.getByLabel("Confirm password").fill("e2e password 123")
  await page.getByRole("button", { name: "Sign up" }).click()
  await expect(page).toHaveURL(/\/chat$/)

  await page.getByRole("link", { name: "Documents" }).click()
  await page.locator('input[type="file"]').setInputFiles({
    name: "refunds.md",
    mimeType: "text/markdown",
    buffer: Buffer.from(NOTES),
  })
  await expect(page.getByRole("row", { name: /refunds\.md/ }).getByText("Ready")).toBeVisible({ timeout: 60_000 })

  await page.getByRole("link", { name: "New chat" }).click()
  await page.getByLabel("Your question").fill("How long do I have to get a refund on the Pro plan?")
  await page.getByRole("button", { name: "Send question" }).click()

  await expect(page.getByText(/30 days/).first()).toBeVisible({ timeout: 60_000 })
  await expect(page.getByRole("button", { name: /refunds\.md · Refunds/ }).first()).toBeVisible({ timeout: 60_000 })
})
