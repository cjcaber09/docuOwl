import { useRef, useState, type DragEvent } from "react"
import { Upload } from "lucide-react"
import { Button } from "@/components/ui/button"
import { notConnected } from "@/lib/notConnected"
import { cn } from "@/lib/utils"

export function UploadDropzone() {
  // Only this component needs to know about dragging, so it's local state, not Zustand.
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setIsDragging(false)
    notConnected("Uploading")
  }

  return (
    <div
      onDragOver={(event) => {
        event.preventDefault()
        setIsDragging(true)
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      className={cn(
        "flex flex-col items-center gap-3 rounded-lg border-2 border-dashed p-8 text-center transition-colors",
        isDragging ? "border-primary bg-primary/5" : "border-border",
      )}
    >
      <Upload className="size-8 text-muted-foreground" />
      <div>
        <p className="font-medium">Drop files here to upload</p>
        <p className="text-sm text-muted-foreground">PDF, DOCX, TXT or MD · up to 20 MB each</p>
      </div>
      <Button variant="outline" onClick={() => fileInputRef.current?.click()}>
        Choose files
      </Button>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.txt,.md"
        multiple
        className="hidden"
        onChange={(event) => {
          if (event.target.files?.length) notConnected("Uploading")
          event.target.value = ""
        }}
      />
    </div>
  )
}
