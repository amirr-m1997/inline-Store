import { test, expect } from "playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("FAQ and technical knowledge", () => {
  test("Persian FAQ page renders and supports native disclosure", async ({ page }, testInfo) => {
    await page.goto("/fa/faq");
    await expect(page.getByRole("heading", { name: "سوالات متداول" })).toBeVisible();
    const summary = page.locator(".faq-disclosure summary").first();
    await expect(summary).toBeVisible();
    await summary.click();
    await expect(page.locator(".faq-disclosure").first()).toHaveAttribute("open", "");
    await expect(page.getByText("پاسخ فنی نمونه")).toBeVisible();
    await expect(new AxeBuilder({ page }).analyze()).resolves.toMatchObject({ violations: [] });
    const screenshotPath = testInfo.project.name === "mobile-chromium" ? "/tmp/phase114-faq-fa-mobile.png" : "/tmp/phase114-faq-fa-desktop.png";
    await page.screenshot({ path: screenshotPath, fullPage: true });
  });

  test("English FAQ page and mobile layout are accessible", async ({ page }, testInfo) => {
    await page.goto("/en/faq");
    await expect(page.getByRole("heading", { name: "Frequently Asked Questions" })).toBeVisible();
    await expect(page.locator("html")).toHaveAttribute("dir", "ltr");
    await expect(new AxeBuilder({ page }).analyze()).resolves.toMatchObject({ violations: [] });
    if (testInfo.project.name === "mobile-chromium") await page.screenshot({ path: "/tmp/phase114-faq-en-mobile.png", fullPage: true });
    else await page.screenshot({ path: "/tmp/phase114-faq-en-desktop.png", fullPage: true });
  });

  test("product context and unified search expose FAQ links", async ({ page }) => {
    await page.goto("/fa/product/test-product");
    await expect(page.getByRole("heading", { name: "سوالات متداول این محصول" })).toBeVisible();
    await page.goto("/fa/search?q=فنی");
    await expect(page.getByRole("heading", { name: "سوالات متداول" })).toBeVisible();
    await expect(page.getByRole("link", { name: "پرسش فنی نمونه" })).toHaveAttribute("href", "/fa/faq#faq-demo-faq");
    await page.screenshot({ path: "/tmp/phase114-search-faq.png", fullPage: true });
  });

  test("mobile FAQ route has no horizontal overflow", async ({ page }) => {
    await page.goto("/fa/product/test-product");
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
    await page.screenshot({ path: "/tmp/phase114-product-faq.png", fullPage: true });
  });
});
