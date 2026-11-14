import { defineConfig, devices } from "playwright/test";

const localChrome = process.env.CI ? {} : { channel: "chrome" as const };

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  use: { baseURL: process.env.E2E_BASE_URL || "http://localhost:3100", trace: "on-first-retry" },
  // Use the locally installed stable Chrome for desktop development without
  // downloading another browser. CI keeps its Playwright-managed browser.
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"], ...localChrome } }, { name: "mobile-chromium", use: { ...devices["Pixel 5"], ...localChrome } }],
  webServer: process.env.E2E_BASE_URL ? undefined : { command: "node tests/e2e/test-server.mjs", url: "http://localhost:3100/fa", reuseExistingServer: true, timeout: 120_000 },
});
