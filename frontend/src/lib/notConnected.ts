import { toast } from "sonner"

// Placeholder for actions that need the backend (build steps 5–7).
export function notConnected(feature: string) {
  toast.info(`${feature} will work once the backend is connected.`)
}
