import { expect, test, type Page } from "playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function assertClean(page: Page) {
  const result = await new AxeBuilder({ page }).analyze();
  expect(result.violations).toEqual([]);
}

function screenshot(testInfo: { project: { name: string } }, desktop: string, mobile: string) {
  return testInfo.project.name === "mobile-chromium" ? mobile : desktop;
}

test.describe("Phase 11.8 final content platform QA", () => {
  test("Knowledge route is localized, database-backed, and accessible", async ({ page }, testInfo) => {
    await page.goto("/fa/knowledge");
    await expect(page.getByRole("heading", { level: 1, name: "دانش و اخبار" })).toBeVisible();
    await expect(page.locator(".editorial-card").first()).toBeVisible();
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    await assertClean(page);
    await page.screenshot({ path: screenshot(testInfo, "/tmp/phase118-knowledge-fa-desktop.png", "/tmp/phase118-knowledge-fa-mobile.png"), fullPage: true });
  });

  test("Unified Search remains compact and grouped", async ({ page }, testInfo) => {
    await page.goto("/fa/search?q=فنی");
    await expect(page.getByRole("heading", { level: 1 })).toContainText("فنی");
    await expect(page.getByRole("heading", { name: "سوالات متداول" })).toBeVisible();
    await expect(page.locator(".site-search-page")).toBeVisible();
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    await assertClean(page);
    await page.screenshot({ path: screenshot(testInfo, "/tmp/phase118-search-fa-desktop.png", "/tmp/phase118-search-fa-mobile.png"), fullPage: true });
  });

  test("FAQ route renders native disclosures and valid schema", async ({ page }, testInfo) => {
    await page.goto("/fa/faq");
    await expect(page.getByRole("heading", { level: 1, name: "سوالات متداول" })).toBeVisible();
    await expect(page.locator(".faq-disclosure").first()).toBeVisible();
    await expect(page.locator('script[type="application/ld+json"]')).toHaveCount(1);
    await assertClean(page);
    await page.screenshot({ path: screenshot(testInfo, "/tmp/phase118-faq-fa-desktop.png", "/tmp/phase118-faq-fa-mobile.png"), fullPage: true });
  });

  test("Resources and compatibility route remain canonical", async ({ page }, testInfo) => {
    await page.goto("/fa/resources");
    await expect(page.getByRole("heading", { level: 1, name: "منابع فنی" })).toBeVisible();
    await expect(page.getByRole("link", { name: /دانلود|Download/ }).first()).toBeVisible();
    await assertClean(page);
    await page.screenshot({ path: screenshot(testInfo, "/tmp/phase118-resources-fa-desktop.png", "/tmp/phase118-resources-fa-mobile.png"), fullPage: true });
    await page.goto("/fa/support/resources");
    await expect(page).toHaveURL(/\/fa\/resources$/);
  });

  test("PDP discovery remains bounded and accessible", async ({ page }, testInfo) => {
    await page.goto("/fa/product/test-product");
    await expect(page.getByRole("heading", { name: "سوالات متداول این محصول" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "منابع فنی مرتبط" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "مطالب مرتبط" })).toBeVisible();
    await assertClean(page);
    await page.screenshot({ path: screenshot(testInfo, "/tmp/phase118-pdp-discovery-fa-desktop.png", "/tmp/phase118-pdp-discovery-fa-mobile.png"), fullPage: true });
  });

  test("Events and English content remain available", async ({ page }, testInfo) => {
    await page.goto("/fa/events");
    await expect(page.getByRole("heading", { level: 1, name: "رویدادها و نمایشگاه‌ها" })).toBeVisible();
    await assertClean(page);
    await page.screenshot({ path: screenshot(testInfo, "/tmp/phase118-events-fa-desktop.png", "/tmp/phase118-events-fa-mobile.png"), fullPage: true });
    await page.goto("/en/knowledge");
    await expect(page.locator("html")).toHaveAttribute("dir", "ltr");
    await expect(page.getByRole("heading", { level: 1, name: "Knowledge & News" })).toBeVisible();
  });

  test("dark theme keeps Phase 11 surfaces readable", async ({ page }) => {
    await page.goto("/fa/resources");
    await page.evaluate(() => window.localStorage.setItem("theme", "dark"));
    await page.reload();
    await expect(page.locator("html")).toHaveClass(/dark/);
    await assertClean(page);
    await page.goto("/fa/knowledge");
    await expect(page.locator("html")).toHaveClass(/dark/);
    await assertClean(page);
    await page.screenshot({ path: "/tmp/phase118-dark-theme.png", fullPage: true });
  });
});
