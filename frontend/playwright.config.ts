import { defineConfig, devices } from "playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  use: { baseURL: process.env.E2E_BASE_URL || "http://localhost:3100", trace: "on-first-retry" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }, { name: "mobile-chromium", use: { ...devices["Pixel 5"] } }],
  webServer: process.env.E2E_BASE_URL ? undefined : { command: "node tests/e2e/test-server.mjs", url: "http://localhost:3100/fa", reuseExistingServer: true, timeout: 120_000 },
});
