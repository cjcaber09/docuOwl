import { Download, FileText } from "lucide-react"
import { DeleteDocumentDialog } from "@/components/DeleteDocumentDialog"
import { StatusBadge } from "@/components/StatusBadge"
import { UploadDropzone } from "@/components/UploadDropzone"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { sampleConfig, sampleDocuments } from "@/data/sampleData"
import { formatDate } from "@/lib/format"
import { notConnected } from "@/lib/notConnected"

export function DocumentsPage() {
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-4 md:p-8">
      <div>
        <h1 className="text-2xl font-semibold">Documents</h1>
        <p className="text-muted-foreground">Owl answers questions using only these files.</p>
      </div>

      <UploadDropzone />

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
          {sampleDocuments.map((document) => (
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
              <TableCell className="hidden sm:table-cell">{formatDate(document.uploadedAt)}</TableCell>
              <TableCell>
                <div className="flex justify-end gap-1">
                  {sampleConfig.storageEnabled && document.status === "ready" && (
                    <Button
                      variant="ghost"
                      size="icon"
                      aria-label={`Download ${document.filename}`}
                      onClick={() => notConnected("Downloading")}
                    >
                      <Download />
                    </Button>
                  )}
                  <DeleteDocumentDialog filename={document.filename} />
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
