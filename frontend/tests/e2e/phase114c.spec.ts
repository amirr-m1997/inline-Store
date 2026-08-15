import { expect, test } from "playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function switchTheme(page: import("playwright").Page, theme: "dark" | "light") {
  await page.evaluate((value) => localStorage.setItem("theme", value), theme);
  await page.reload();
  if (theme === "dark") {
    await expect(page.locator("html")).toHaveClass(/dark/);
  } else {
    await expect(page.locator("html")).not.toHaveClass(/dark/);
  }
}

async function assertContrast(page: import("playwright").Page) {
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
}

test.describe("Phase 11.4C dark-theme contrast", () => {
  test("audits dark and light search surfaces plus the shared desktop header", async ({ page }, testInfo) => {
    const mobile = testInfo.project.name === "mobile-chromium";
    await page.setViewportSize(mobile ? { width: 390, height: 844 } : { width: 1440, height: 900 });
    await page.goto("/fa/search?q=فنی");
    await switchTheme(page, "dark");
    await expect(page.getByRole("heading", { name: "محصولات" })).toBeVisible();
    await expect(page.getByRole("link", { name: /دسته‌بندی‌ها/ }).first()).toBeVisible();
    await assertContrast(page);
    if (mobile) {
      await page.screenshot({ path: "/tmp/phase114c-search-dark-fa-mobile.png", fullPage: true });
      return;
    }
    await page.screenshot({ path: "/tmp/phase114c-search-dark-fa-desktop.png", fullPage: true });

    await switchTheme(page, "light");
    await page.goto("/fa/search?q=فنی");
    await assertContrast(page);
    await page.screenshot({ path: "/tmp/phase114c-search-light-fa-desktop.png", fullPage: true });

    await page.goto("/en/search?q=technical");
    await switchTheme(page, "dark");
    await assertContrast(page);
    await page.screenshot({ path: "/tmp/phase114c-search-dark-en-desktop.png", fullPage: true });
  });

  test("audits active navigation and header controls in Persian dark theme", async ({ page }, testInfo) => {
    const mobile = testInfo.project.name === "mobile-chromium";
    await page.setViewportSize(mobile ? { width: 390, height: 844 } : { width: 1440, height: 900 });
    await page.goto("/fa/knowledge");
    await switchTheme(page, "dark");
    if (mobile) {
      await page.getByRole("button", { name: "باز کردن منو" }).click();
    }
    const bestDiscounts = page.getByRole("link", { name: "بیشترین تخفیف" }).first();
    await bestDiscounts.hover();
    const hoverColor = await bestDiscounts.evaluate((element) => getComputedStyle(element).color);
    const hoverRgb = hoverColor.match(/\d+/g)?.map(Number) ?? [];
    expect(hoverRgb.length).toBe(3);
    expect(hoverRgb.reduce((sum, value) => sum + value, 0)).toBeGreaterThan(300);
    const categoryTrigger = page.getByRole("button", { name: /دسته‌بندی محصولات/ }).first();
    await categoryTrigger.hover();
    await expect(categoryTrigger.locator("b")).toHaveCSS("color", "rgb(255, 255, 255)");
    const active = page.locator('.reference-primary-links a[aria-current="page"]');
    await expect(page.locator('.reference-primary-links a[aria-current="page"]')).toHaveText("دانش و اخبار");
    await assertContrast(page);
    await page.screenshot({ path: mobile ? "/tmp/phase114c-header-dark-fa-mobile.png" : "/tmp/phase114c-header-dark-fa-desktop.png", fullPage: true });
    if (mobile) return;

    await page.goto("/en/knowledge");
    await switchTheme(page, "dark");
    await expect(page.locator('.reference-primary-links a[aria-current="page"]')).toHaveText("Knowledge & News");
    await assertContrast(page);
    await page.screenshot({ path: "/tmp/phase114c-header-dark-en-desktop.png", fullPage: true });

    await page.goto("/fa/knowledge");
    await switchTheme(page, "light");
    await assertContrast(page);
    await page.screenshot({ path: "/tmp/phase114c-header-light-fa-desktop.png", fullPage: true });
  });
});
