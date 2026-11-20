import { Download, FileText } from "lucide-react"
import { ConfirmDeleteDialog } from "@/components/ConfirmDeleteDialog"
import { StatusBadge } from "@/components/StatusBadge"
import { UploadDropzone } from "@/components/UploadDropzone"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useAppConfig } from "@/hooks/useAppConfig"
import { useDeleteDocument, useDocuments, useUploadDocument, useUploadsInProgress } from "@/hooks/useDocuments"
import type { OwlDocument } from "@/lib/apiTypes"
import { formatDate } from "@/lib/format"
import { notConnected } from "@/lib/notConnected"

export function DocumentsPage() {
  const storageEnabled = useAppConfig().data?.storageEnabled ?? false
  const documents = useDocuments()
  const upload = useUploadDocument()
  const uploading = useUploadsInProgress()
  const deleteDocument = useDeleteDocument()

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-4 md:p-8">
      <div>
        <h1 className="text-2xl font-semibold">Documents</h1>
        <p className="text-muted-foreground">Owl answers questions using only these files.</p>
      </div>

      <UploadDropzone onFiles={(files) => files.forEach((file) => upload.mutate(file))} />
      {uploading > 0 && (
        <p className="text-sm text-muted-foreground">
          Uploading {uploading} {uploading === 1 ? "file" : "files"}…
        </p>
      )}

      {documents.isPending ? (
        <p className="text-muted-foreground">Loading your documents…</p>
      ) : documents.isError ? (
        <p className="text-destructive">Couldn't load your documents. {documents.error.message}</p>
      ) : documents.data.length === 0 ? (
        <p className="text-muted-foreground">No documents yet. Upload a file to get started.</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="hidden sm:table-cell">Pages</TableHead>
              <TableHead className="hidden sm:table-cell">Uploaded</TableHead>
              <TableHead className="text-right">
                <span className="sr-only">Actions</span>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {documents.data.map((document: OwlDocument) => (
              <TableRow key={document.id}>
                <TableCell className="whitespace-normal">
                  <div className="flex items-start gap-2">
                    <FileText className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                    <div className="min-w-0">
                      <p className="font-medium break-all">{document.filename}</p>
                      {document.failureReason && <p className="text-sm text-destructive">{document.failureReason}</p>}
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <StatusBadge status={document.status} />
                </TableCell>
                <TableCell className="hidden sm:table-cell">{document.pageCount ?? "—"}</TableCell>
                <TableCell className="hidden sm:table-cell">{formatDate(document.createdAt)}</TableCell>
                <TableCell>
                  <div className="flex justify-end gap-1">
                    {storageEnabled && document.status === "ready" && (
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={`Download ${document.filename}`}
                        onClick={() => notConnected("Downloading")}
                      >
                        <Download />
                      </Button>
                    )}
                    <ConfirmDeleteDialog
                      itemName={document.filename}
                      description="Owl will forget everything in this file. Earlier answers that cited it stay readable."
                      onConfirm={() => deleteDocument.mutate(document.id)}
                    />
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
