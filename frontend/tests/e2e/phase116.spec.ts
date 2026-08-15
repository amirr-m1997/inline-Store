import { expect, test } from "playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("Phase 11.6 technical resources", () => {
    test("resources are discoverable, filterable, and accessible", async ({ page }) => {
      await page.goto("/fa/resources");
      await expect(page.getByRole("heading", { level: 1, name: "منابع فنی" })).toBeVisible();
      await expect(page.getByRole("form", { name: "فیلتر منابع فنی" })).toBeVisible();
      await expect(new AxeBuilder({ page }).analyze()).resolves.toMatchObject({ violations: [] });
      await page.screenshot({ path: test.info().project.name === "chromium" ? "/tmp/phase116-resources-fa-desktop.png" : "/tmp/phase116-resources-fa-mobile.png", fullPage: true });
    });

    test("legacy resources route redirects to the canonical route", async ({ page }) => {
      await page.goto("/fa/support/resources");
      await expect(page).toHaveURL(/\/fa\/resources$/);
    });
});

test("English resources, events, and dark theme remain available", async ({ page }) => {
  await page.goto("/en/resources");
  await expect(page.getByRole("heading", { level: 1, name: "Technical Resources" })).toBeVisible();
  await page.screenshot({ path: test.info().project.name === "chromium" ? "/tmp/phase116-resources-en-desktop.png" : "/tmp/phase116-resources-en-mobile.png", fullPage: true });
  await page.goto("/fa/events");
  await expect(page.getByRole("heading", { level: 1, name: "رویدادها و نمایشگاه‌ها" })).toBeVisible();
  await page.screenshot({ path: test.info().project.name === "chromium" ? "/tmp/phase116-events-fa-desktop.png" : "/tmp/phase116-events-fa-mobile.png", fullPage: true });
  await page.evaluate(() => window.localStorage.setItem("theme", "dark"));
  await page.reload();
  await expect(page.locator("html")).toHaveClass(/dark/);
  await expect(new AxeBuilder({ page }).analyze()).resolves.toMatchObject({ violations: [] });
  await page.goto("/fa/resources");
  await page.evaluate(() => window.localStorage.setItem("theme", "dark"));
  await page.reload();
  await expect(page.locator("html")).toHaveClass(/dark/);
  await expect(new AxeBuilder({ page }).analyze()).resolves.toMatchObject({ violations: [] });
  await page.screenshot({ path: "/tmp/phase116-resources-dark.png", fullPage: true });
});
