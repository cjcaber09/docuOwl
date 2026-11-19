import { QueryCache, QueryClient } from "@tanstack/react-query"
import { ApiError } from "@/lib/api"

export const CURRENT_USER_KEY = ["auth", "me"] as const

export function createQueryClient(): QueryClient {
  const client: QueryClient = new QueryClient({
    queryCache: new QueryCache({
      onError: (error) => {
        // A 401 from any request means the session ended: forget everything, then show the login page.
        if (error instanceof ApiError && error.status === 401) {
          client.clear()
          client.setQueryData(CURRENT_USER_KEY, null)
        }
      },
    }),
    defaultOptions: {
      queries: { retry: false, refetchOnWindowFocus: false },
    },
  })
  return client
}

export const queryClient = createQueryClient()
