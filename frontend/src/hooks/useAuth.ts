import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "react-router"
import { ApiError, apiFetch } from "@/lib/api"
import type { User } from "@/lib/apiTypes"
import { CURRENT_USER_KEY } from "@/lib/queryClient"
import type { LoginValues, SignupValues } from "@/lib/validation"

/** The logged-in user, or null when nobody is logged in. */
export function useCurrentUser() {
  return useQuery({
    queryKey: CURRENT_USER_KEY,
    queryFn: async () => {
      try {
        return await apiFetch<User>("/auth/me")
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) return null
        throw error
      }
    },
    staleTime: Infinity,
  })
}

/** After login or sign-up: remember who is logged in, then open the chat. */
function useEnterApp() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  return (user: User) => {
    queryClient.setQueryData(CURRENT_USER_KEY, user)
    navigate("/chat", { replace: true })
  }
}

export function useLogin() {
  const enterApp = useEnterApp()
  return useMutation({
    mutationFn: (values: LoginValues) => apiFetch<User>("/auth/login", { method: "POST", body: values }),
    onSuccess: enterApp,
  })
}

export function useSignup() {
  const enterApp = useEnterApp()
  return useMutation({
    mutationFn: ({ email, password }: SignupValues) =>
      apiFetch<User>("/auth/signup", { method: "POST", body: { email, password } }),
    onSuccess: enterApp,
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  return useMutation({
    mutationFn: () => apiFetch<null>("/auth/logout", { method: "POST" }),
    onSettled: () => {
      // Forget every piece of this user's data so the next person on this browser sees none of it.
      queryClient.clear()
      queryClient.setQueryData(CURRENT_USER_KEY, null)
      navigate("/login", { replace: true })
    },
  })
}
