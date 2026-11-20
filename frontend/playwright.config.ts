import { defineConfig, devices } from "@playwright/test"

const API_PORT = 8010
const WEB_PORT = 5174

export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  use: { baseURL: `http://localhost:${WEB_PORT}`, trace: "retain-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      // The TEST database (.env.test's DATABASE_URL wins over .env) and the real Voyage key from .env.
      command: `uv run --env-file .env.test fastapi run app/main.py --port ${API_PORT}`,
      cwd: "../backend",
      url: `http://localhost:${API_PORT}/api/health`,
      env: {
        FRONTEND_URL: `http://localhost:${WEB_PORT}`,
        // Free by default: demo answers quote the best passage. CHAT_MODEL=claude npm run e2e uses Claude.
        CHAT_MODEL: process.env.CHAT_MODEL ?? "demo",
      },
      timeout: 120_000,
      reuseExistingServer: false,
    },
    {
      command: `npm run dev -- --port ${WEB_PORT} --strictPort`,
      url: `http://localhost:${WEB_PORT}`,
      env: { OWL_API_URL: `http://localhost:${API_PORT}` },
      reuseExistingServer: false,
    },
  ],
})
