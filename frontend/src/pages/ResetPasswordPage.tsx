import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { Link, useSearchParams } from "react-router"
import { FormField } from "@/components/FormField"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { notConnected } from "@/lib/notConnected"
import { resetPasswordSchema, type ResetPasswordValues } from "@/lib/validation"

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get("token")
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordValues>({ resolver: zodResolver(resetPasswordSchema) })

  return (
    <Card>
      <CardHeader>
        <CardTitle>Set a new password</CardTitle>
        <CardDescription>After this, you'll be logged out on all your devices.</CardDescription>
      </CardHeader>
      <CardContent>
        {token ? (
          <form onSubmit={handleSubmit(() => notConnected("Password reset"))} className="grid gap-4" noValidate>
            <FormField
              id="password"
              label="New password"
              type="password"
              autoComplete="new-password"
              error={errors.password?.message}
              {...register("password")}
            />
            <FormField
              id="confirmPassword"
              label="Confirm new password"
              type="password"
              autoComplete="new-password"
              error={errors.confirmPassword?.message}
              {...register("confirmPassword")}
            />
            <Button type="submit">Save new password</Button>
          </form>
        ) : (
          <p className="text-sm text-destructive">
            This reset link is missing its code. Use the link from your email, or request a new one.
          </p>
        )}
      </CardContent>
      <CardFooter className="justify-center text-sm">
        <Link to="/forgot-password" className="text-primary underline-offset-4 hover:underline">
          Request a new link
        </Link>
      </CardFooter>
    </Card>
  )
}
