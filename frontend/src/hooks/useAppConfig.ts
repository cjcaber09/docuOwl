import { useQuery } from "@tanstack/react-query"
import { apiFetch } from "@/lib/api"
import type { AppConfig } from "@/lib/apiTypes"

/** Which optional features the backend has turned on. */
export function useAppConfig() {
  return useQuery({
    queryKey: ["config"],
    queryFn: () => apiFetch<AppConfig>("/config"),
    staleTime: Infinity,
  })
}
