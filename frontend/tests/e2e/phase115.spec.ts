import { expect, test } from "playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("Phase 11.5 public editorial surfaces remain reviewable", async ({ page }) => {
  test.skip(test.info().project.name !== "chromium", "Phase 11.5 screenshot baseline is captured once in desktop Chromium.");
  for (const [path, screenshot, heading] of [
    ["/fa/knowledge", "/tmp/phase115-knowledge-fa.png", "دانش و اخبار"],
    ["/fa/news", "/tmp/phase115-news-fa.png", "اخبار و رویدادها"],
    ["/fa/faq", "/tmp/phase115-faq-fa.png", "سوالات متداول"],
    ["/fa/search?q=فنی", "/tmp/phase115-search-content-fa.png", "نتایج برای «فنی»"],
  ] as const) {
    await page.goto(path);
    await expect(page.getByRole("heading", { level: 1, name: heading })).toBeVisible();
    await expect(new AxeBuilder({ page }).analyze()).resolves.toMatchObject({ violations: [] });
    await page.screenshot({ path: screenshot, fullPage: true });
  }

  await page.goto("/fa/knowledge");
  await page.evaluate(() => window.localStorage.setItem("theme", "dark"));
  await page.reload();
  await expect(page.locator("html")).toHaveClass(/dark/);
  await expect(new AxeBuilder({ page }).analyze()).resolves.toMatchObject({ violations: [] });
  await page.screenshot({ path: "/tmp/phase115-dark-theme.png", fullPage: true });
});
