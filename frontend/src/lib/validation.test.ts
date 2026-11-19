import { describe, expect, it } from "vitest"
import { loginSchema, signupSchema } from "@/lib/validation"

describe("signupSchema", () => {
  it("accepts a valid sign-up", () => {
    const result = signupSchema.safeParse({
      email: "reader@example.com",
      password: "long enough pw",
      confirmPassword: "long enough pw",
    })

    expect(result.success).toBe(true)
  })

  it("rejects passwords shorter than 10 characters", () => {
    const result = signupSchema.safeParse({ email: "reader@example.com", password: "short", confirmPassword: "short" })

    expect(result.error?.issues[0].message).toBe("Use at least 10 characters")
  })

  it("rejects passwords that don't match", () => {
    const result = signupSchema.safeParse({
      email: "reader@example.com",
      password: "long enough pw",
      confirmPassword: "something else",
    })

    expect(result.error?.issues[0].message).toBe("Passwords don't match")
  })
})

describe("loginSchema", () => {
  it("rejects an invalid email", () => {
    const result = loginSchema.safeParse({ email: "not-an-email", password: "x" })

    expect(result.error?.issues[0].message).toBe("Enter a valid email address")
  })
})
