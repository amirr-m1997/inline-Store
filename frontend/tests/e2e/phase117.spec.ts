import { test, expect, type Page } from "playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function expectAxeClean(page: Page, selectors?: string[]) {
  const builder = new AxeBuilder({ page });
  if (selectors) builder.include(selectors);
  const result = await builder.analyze();
  expect(result.violations).toEqual([]);
}

test.describe("Phase 11.7 related discovery", () => {
  test("product exposes bounded article, FAQ, and technical-resource discovery", async ({ page }, testInfo) => {
    await page.goto("/fa/product/test-product");
    await expect(page.getByRole("heading", { name: "سوالات متداول این محصول" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "مطالب مرتبط" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "منابع فنی مرتبط" })).toBeVisible();
    await expect(page.getByRole("link", { name: /دانلود/ }).first()).toHaveAttribute("href", /demo-datasheet/);
    await expectAxeClean(page, [".discovery-section", ".faq-list", ".editorial-preview"]);
    await page.screenshot({ path: testInfo.project.name === "chromium" ? "/tmp/phase117-pdp-related-fa-desktop.png" : "/tmp/phase117-pdp-related-fa-mobile.png", fullPage: true });
  });

  test("article exposes related product discovery without internal diagnostics", async ({ page }, testInfo) => {
    await page.goto("/fa/knowledge/demo-technical-article");
    await expect(page.getByRole("heading", { name: "محصولات مرتبط" }).last()).toBeVisible();
    await expect(page.getByRole("link", { name: /محصول تست/ }).first()).toHaveAttribute("href", "/fa/product/test-product");
    await expect(page.getByText("direct_product")).toHaveCount(0);
    await expectAxeClean(page, [".discovery-section"]);
    await page.screenshot({ path: testInfo.project.name === "chromium" ? "/tmp/phase117-article-related-fa-desktop.png" : "/tmp/phase117-article-related-fa-mobile.png", fullPage: true });
  });

  test("related surfaces remain readable in dark theme", async ({ page }, testInfo) => {
    await page.goto("/fa/product/test-product");
    await page.evaluate(() => window.localStorage.setItem("theme", "dark"));
    await page.reload();
    await expect(page.locator("html")).toHaveClass(/dark/);
    await expectAxeClean(page, [".discovery-section"]);
    await page.screenshot({ path: "/tmp/phase117-dark-theme.png", fullPage: true });
  });
});
