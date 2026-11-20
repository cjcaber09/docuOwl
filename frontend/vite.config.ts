import path from "node:path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vitest/config"

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  server: {
    // The browser only ever talks to Vite's address; Vite passes /api requests on to the backend.
    proxy: {
      "/api": process.env.OWL_API_URL ?? "http://localhost:8000",
    },
  },
  test: {
    environment: "jsdom",
    // Only unit tests; the Playwright tests in e2e/ run with `npm run e2e`.
    include: ["src/**/*.test.{ts,tsx}"],
    setupFiles: ["./src/test/setup.ts"],
  },
})
