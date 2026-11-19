import { useIsMutating, useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { apiFetch } from "@/lib/api"
import type { OwlDocument } from "@/lib/apiTypes"

export const DOCUMENTS_KEY = ["documents"] as const
const UPLOAD_KEY = ["upload-document"] as const
const POLL_WHILE_PROCESSING_MS = 3000

export function useDocuments() {
  return useQuery({
    queryKey: DOCUMENTS_KEY,
    queryFn: () => apiFetch<OwlDocument[]>("/documents"),
    // Ask again every few seconds while any file is still processing, then stop.
    refetchInterval: (query) =>
      query.state.data?.some((document) => document.status === "processing") ? POLL_WHILE_PROCESSING_MS : false,
  })
}

export function useUploadDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: UPLOAD_KEY,
    mutationFn: (file: File) => {
      const form = new FormData()
      form.append("file", file)
      return apiFetch<OwlDocument>("/documents", { method: "POST", body: form })
    },
    // These run for every file, even when several upload at once.
    onError: (error, file) => toast.error(`${file.name}: ${error.message}`),
    onSettled: () => queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY }),
  })
}

/** How many uploads are still being sent. */
export function useUploadsInProgress() {
  return useIsMutating({ mutationKey: UPLOAD_KEY })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiFetch<null>(`/documents/${id}`, { method: "DELETE" }),
    onError: (error) => toast.error(error.message),
    onSettled: () => queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY }),
  })
}
