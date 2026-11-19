import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { Link } from "react-router"
import { FormError } from "@/components/FormError"
import { FormField } from "@/components/FormField"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { useAppConfig } from "@/hooks/useAppConfig"
import { useLogin } from "@/hooks/useAuth"
import { loginSchema, type LoginValues } from "@/lib/validation"

export function LoginPage() {
  const config = useAppConfig()
  const login = useLogin()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginValues>({ resolver: zodResolver(loginSchema) })

  return (
    <Card>
      <CardHeader>
        <CardTitle>Log in</CardTitle>
        <CardDescription>Chat with your own documents.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit((values) => login.mutate(values))} className="grid gap-4" noValidate>
          <FormField id="email" label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register("email")} />
          <FormField
            id="password"
            label="Password"
            type="password"
            autoComplete="current-password"
            error={errors.password?.message}
            {...register("password")}
          />
          {config.data?.emailEnabled && (
            <Link to="/forgot-password" className="text-sm text-primary underline-offset-4 hover:underline">
              Forgot password?
            </Link>
          )}
          <FormError message={login.error?.message} />
          <Button type="submit" disabled={login.isPending}>
            {login.isPending ? "Logging in…" : "Log in"}
          </Button>
        </form>
      </CardContent>
      <CardFooter className="justify-center text-sm text-muted-foreground">
        No account yet?&nbsp;
        <Link to="/signup" className="text-primary underline-offset-4 hover:underline">
          Sign up
        </Link>
      </CardFooter>
    </Card>
  )
}
