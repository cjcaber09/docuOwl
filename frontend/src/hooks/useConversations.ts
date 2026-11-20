import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { apiFetch } from "@/lib/api"
import type { Conversation, ConversationSummary } from "@/lib/apiTypes"

export const CONVERSATIONS_KEY = ["conversations"] as const

export function conversationKey(id: string) {
  return ["conversations", id] as const
}

export function useConversations() {
  return useQuery({
    queryKey: CONVERSATIONS_KEY,
    queryFn: () => apiFetch<ConversationSummary[]>("/conversations"),
  })
}

export function useConversation(id: string | undefined) {
  return useQuery({
    queryKey: conversationKey(id ?? ""),
    queryFn: () => apiFetch<Conversation>(`/conversations/${id}`),
    enabled: Boolean(id),
  })
}

export function useDeleteConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiFetch<null>(`/conversations/${id}`, { method: "DELETE" }),
    onSuccess: (_data, id) => queryClient.removeQueries({ queryKey: conversationKey(id) }),
    onError: (error) => toast.error(error.message),
    onSettled: () => queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY }),
  })
}
