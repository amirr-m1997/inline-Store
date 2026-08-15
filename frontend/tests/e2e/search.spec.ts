import { expect, test } from "playwright/test";
import AxeBuilder from "@axe-core/playwright";
import type { Page } from "playwright";

async function assertAxe(page: Page) {
  const results = await new AxeBuilder({ page }).disableRules(["color-contrast"]).analyze();
  expect(results.violations).toEqual([]);
}

test.describe("unified storefront search", () => {
  test("Persian product search submits from the header and groups results", async ({ page }, testInfo) => {
    await page.goto("/fa");
    await page.locator("#site-search").fill("چیلر");
    await page.locator("#site-search").press("Enter");
    await expect(page).toHaveURL(/\/fa\/search\?q=/);
    await expect(page.getByRole("heading", { name: /نتایج برای/ })).toBeVisible();
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(page.getByText(/نتیجه/).first()).toBeVisible();
    await expect(page.getByRole("heading", { name: "محصولات" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "دانش و اخبار" })).toBeVisible();
    await expect(page.locator(".site-search-form")).toHaveCount(0);
    const suffix = testInfo.project.name === "mobile-chromium" ? "mobile" : "desktop";
    await page.screenshot({ path: `/tmp/phase114b-search-fa-${suffix}.png`, fullPage: true });
    if (suffix === "desktop") await page.screenshot({ path: "/tmp/phase114b-search-fa-multi-group.png", fullPage: true });
    await assertAxe(page);
  });

  test("English search and technical identifier remain LTR-safe", async ({ page }) => {
    await page.goto("/en/search?q=MPN-CH-42");
    await expect(page.locator("html")).toHaveAttribute("dir", "ltr");
    await expect(page.getByRole("heading", { name: /Results for/ })).toBeVisible();
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(page.locator('bdi[dir="ltr"]').filter({ hasText: "T-1" }).first()).toBeVisible();
    await page.screenshot({ path: "/tmp/phase114b-search-en-desktop.png", fullPage: true });
    await assertAxe(page);
  });

  test("no-result state is useful and mobile has no overflow", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/fa/search?q=nothing");
    await expect(page.getByRole("heading", { name: /نتیجه‌ای برای/ })).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
    expect(overflow).toBe(false);
    await page.screenshot({ path: "/tmp/phase114b-search-empty.png", fullPage: true });
    await assertAxe(page);
  });
});
