import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { Link } from "react-router"
import { FormError } from "@/components/FormError"
import { FormField } from "@/components/FormField"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { useSignup } from "@/hooks/useAuth"
import { signupSchema, type SignupValues } from "@/lib/validation"

export function SignupPage() {
  const signup = useSignup()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupValues>({ resolver: zodResolver(signupSchema) })

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create your account</CardTitle>
        <CardDescription>Upload your documents and ask Owl about them.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit((values) => signup.mutate(values))} className="grid gap-4" noValidate>
          <FormField id="email" label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register("email")} />
          <FormField
            id="password"
            label="Password"
            type="password"
            autoComplete="new-password"
            error={errors.password?.message}
            {...register("password")}
          />
          <FormField
            id="confirmPassword"
            label="Confirm password"
            type="password"
            autoComplete="new-password"
            error={errors.confirmPassword?.message}
            {...register("confirmPassword")}
          />
          <p className="text-xs text-muted-foreground">
            To answer your questions, the text of your documents is sent to Voyage AI (for search) and Anthropic (for answers).
          </p>
          <FormError message={signup.error?.message} />
          <Button type="submit" disabled={signup.isPending}>
            {signup.isPending ? "Creating account…" : "Sign up"}
          </Button>
        </form>
      </CardContent>
      <CardFooter className="justify-center text-sm text-muted-foreground">
        Already have an account?&nbsp;
        <Link to="/login" className="text-primary underline-offset-4 hover:underline">
          Log in
        </Link>
      </CardFooter>
    </Card>
  )
}
