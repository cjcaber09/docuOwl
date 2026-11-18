import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { Link } from "react-router"
import { FormField } from "@/components/FormField"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { sampleConfig } from "@/data/sampleData"
import { notConnected } from "@/lib/notConnected"
import { loginSchema, type LoginValues } from "@/lib/validation"

export function LoginPage() {
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
        <form onSubmit={handleSubmit(() => notConnected("Logging in"))} className="grid gap-4" noValidate>
          <FormField id="email" label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register("email")} />
          <FormField
            id="password"
            label="Password"
            type="password"
            autoComplete="current-password"
            error={errors.password?.message}
            {...register("password")}
          />
          {sampleConfig.emailEnabled && (
            <Link to="/forgot-password" className="text-sm text-primary underline-offset-4 hover:underline">
              Forgot password?
            </Link>
          )}
          <Button type="submit">Log in</Button>
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
