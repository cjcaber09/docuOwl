import { z } from "zod"

const email = z.email({ error: "Enter a valid email address" })

const newPassword = z
  .string()
  .min(10, { error: "Use at least 10 characters" })
  .max(128, { error: "Use at most 128 characters" })

export const loginSchema = z.object({
  email,
  password: z.string().min(1, { error: "Enter your password" }),
})

export const signupSchema = z
  .object({
    email,
    password: newPassword,
    confirmPassword: z.string(),
  })
  .refine((values) => values.password === values.confirmPassword, {
    error: "Passwords don't match",
    path: ["confirmPassword"],
  })

export const forgotPasswordSchema = z.object({ email })

export const resetPasswordSchema = z
  .object({
    password: newPassword,
    confirmPassword: z.string(),
  })
  .refine((values) => values.password === values.confirmPassword, {
    error: "Passwords don't match",
    path: ["confirmPassword"],
  })

export type LoginValues = z.infer<typeof loginSchema>
export type SignupValues = z.infer<typeof signupSchema>
export type ForgotPasswordValues = z.infer<typeof forgotPasswordSchema>
export type ResetPasswordValues = z.infer<typeof resetPasswordSchema>
