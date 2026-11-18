import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { Link } from "react-router"
import { FormField } from "@/components/FormField"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { notConnected } from "@/lib/notConnected"
import { forgotPasswordSchema, type ForgotPasswordValues } from "@/lib/validation"

export function ForgotPasswordPage() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordValues>({ resolver: zodResolver(forgotPasswordSchema) })

  return (
    <Card>
      <CardHeader>
        <CardTitle>Forgot your password?</CardTitle>
        <CardDescription>Enter your email and we'll send you a link to set a new one.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(() => notConnected("Password reset"))} className="grid gap-4" noValidate>
          <FormField id="email" label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register("email")} />
          <Button type="submit">Send reset link</Button>
        </form>
      </CardContent>
      <CardFooter className="justify-center text-sm">
        <Link to="/login" className="text-primary underline-offset-4 hover:underline">
          Back to log in
        </Link>
      </CardFooter>
    </Card>
  )
}
