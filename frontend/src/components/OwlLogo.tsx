import owlLogoUrl from "@/assets/owl-logo.svg"
import { cn } from "@/lib/utils"

type OwlLogoProps = {
  className?: string
}

export function OwlLogo({ className }: OwlLogoProps) {
  return <img src={owlLogoUrl} alt="Owl" className={cn("size-10", className)} />
}
