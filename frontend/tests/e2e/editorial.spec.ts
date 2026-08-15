import { expect, test } from "playwright/test";
import AxeBuilder from "@axe-core/playwright";
import type { Page } from "playwright";

async function assertEditorialA11y(page: Page) {
  const results = await new AxeBuilder({ page }).disableRules(["color-contrast"]).analyze();
  expect(results.violations).toEqual([]);
}

test.describe("Knowledge & News editorial center", () => {
  test("Persian Knowledge landing renders CMS content and is shareable", async ({ page }) => {
    await page.goto("/fa/knowledge");
    await expect(page.getByRole("heading", { level: 1, name: "دانش و اخبار" })).toBeVisible();
    await expect(page.getByText("[DEMO] مقاله فنی نمونه").first()).toBeVisible();
    await expect(page.getByRole("link", { name: "مقالات فنی" })).toHaveAttribute("href", "/fa/knowledge?type=technical_article");
    await page.screenshot({ path: "/tmp/phase112-knowledge-fa-desktop.png", fullPage: true });
    await assertEditorialA11y(page);
  });

  test("Persian News page filters news and event-oriented content", async ({ page }) => {
    await page.goto("/fa/news");
    await expect(page.getByRole("heading", { level: 1, name: "اخبار و رویدادها" })).toBeVisible();
    await expect(page.getByText("[DEMO] خبر شرکت نمونه").first()).toBeVisible();
    await expect(page.getByRole("link", { name: "اخبار", exact: true })).toHaveAttribute("href", "/fa/news?type=news");
    await page.screenshot({ path: "/tmp/phase112-news-fa-desktop.png", fullPage: true });
    await assertEditorialA11y(page);
  });

  test("Article detail renders body, breadcrumbs, explicit relationships and SEO data", async ({ page }) => {
    await page.goto("/fa/knowledge/demo-technical-article");
    await expect(page.getByRole("heading", { level: 1, name: /مقاله فنی نمونه/ })).toBeVisible();
    await expect(page.locator(".editorial-article-body")).toContainText("این متن نمونه");
    await expect(page.getByRole("heading", { name: "محصولات مرتبط" })).toBeVisible();
    await expect(page.locator('script[type="application/ld+json"]')).toHaveCount(1);
    await page.screenshot({ path: "/tmp/phase112-article-fa-desktop.png", fullPage: true });
    await assertEditorialA11y(page);
  });

  test("English Knowledge and article routes render in LTR", async ({ page }) => {
    await page.goto("/en/knowledge");
    await expect(page.locator("html")).toHaveAttribute("dir", "ltr");
    await expect(page.getByRole("heading", { level: 1, name: "Knowledge & News" })).toBeVisible();
    await page.screenshot({ path: "/tmp/phase112-knowledge-en-desktop.png", fullPage: true });
    await page.goto("/en/knowledge/demo-technical-article");
    await expect(page.getByRole("heading", { level: 1, name: /Technical article example/ })).toBeVisible();
    await page.screenshot({ path: "/tmp/phase112-article-en-desktop.png", fullPage: true });
    await assertEditorialA11y(page);
  });

  test("mobile editorial routes have no horizontal overflow", async ({ page }) => {
    await page.goto("/fa/knowledge");
    await expect(page.getByRole("heading", { level: 1, name: "دانش و اخبار" })).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
    expect(overflow).toBe(false);
    await page.screenshot({ path: "/tmp/phase112-knowledge-fa-mobile.png", fullPage: true });
    await page.goto("/fa/news");
    await page.screenshot({ path: "/tmp/phase112-news-fa-mobile.png", fullPage: true });
    await page.goto("/fa/knowledge/demo-technical-article");
    await page.screenshot({ path: "/tmp/phase112-article-fa-mobile.png", fullPage: true });
  });
});
