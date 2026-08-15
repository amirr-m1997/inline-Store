import { expect, test } from "playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function assertAxe(page: import("playwright").Page) {
  const results = await new AxeBuilder({ page }).disableRules(["color-contrast"]).analyze();
  expect(results.violations).toEqual([]);
}

test.describe("Phase 11.4A search layout regression", () => {
  test("keeps Persian header controls separated and submits پیچ", async ({ page }, testInfo) => {
    await page.goto("/fa");
    const input = page.locator("#site-search");
    await input.fill("[DEMO] تجهیزات فنی برای انتخاب و نگهداری سامانه صنعتی");
    const clear = page.getByRole("button", { name: "پاک کردن جست‌وجو" });
    const submit = page.getByRole("button", { name: "جست‌وجو", exact: true });
    const clearBox = await clear.boundingBox();
    const submitBox = await submit.boundingBox();
    const formBox = await page.locator(".reference-search").boundingBox();
    expect(clearBox).not.toBeNull();
    expect(submitBox).not.toBeNull();
    expect(formBox).not.toBeNull();
    expect(clearBox!.x + clearBox!.width).toBeLessThanOrEqual(submitBox!.x + submitBox!.width + formBox!.width);
    expect(clearBox!.x + clearBox!.width <= submitBox!.x || submitBox!.x + submitBox!.width <= clearBox!.x).toBeTruthy();
    const expectedPadding = await page.evaluate(() => window.innerWidth <= 767 ? { start: "66px", end: "42px" } : { start: "76px", end: "46px" });
    expect(await input.evaluate((node) => ({ start: getComputedStyle(node).paddingInlineStart, end: getComputedStyle(node).paddingInlineEnd }))).toEqual(expectedPadding);
    await clear.click();
    await expect(input).toHaveValue("");
    await input.fill("پیچ");
    await input.press("Enter");
    await expect(page).toHaveURL(/\/fa\/search\?q=%D9%BE%DB%8C%DA%86/);
    await expect(page.getByRole("heading", { name: "محصولات" })).toBeVisible();
    await assertAxe(page);
    await page.screenshot({ path: "/tmp/phase114a-header-search-fa-long-query.png", fullPage: true });
    await page.screenshot({ path: testInfo.project.name === "mobile-chromium" ? "/tmp/phase114a-search-results-mobile.png" : "/tmp/phase114a-search-results-fa.png", fullPage: true });
    if (testInfo.project.name === "chromium") {
      await page.goto("/fa");
      await input.fill("[DEMO] تجهیزات فنی");
      await page.screenshot({ path: "/tmp/phase114a-header-search-fa-desktop.png", fullPage: true });
    } else {
      await page.goto("/fa");
      await input.fill("[DEMO] تجهیزات فنی");
      await page.screenshot({ path: "/tmp/phase114a-header-search-fa-mobile.png", fullPage: true });
    }
  });

  test("keeps the mobile English header search controls separated", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/en");
    const input = page.locator("#site-search");
    await input.fill("[DEMO] industrial technical equipment selection and maintenance guide");
    const clear = page.getByRole("button", { name: "پاک کردن جست‌وجو" });
    const submit = page.getByRole("button", { name: "جست‌وجو", exact: true });
    const clearBox = await clear.boundingBox();
    const submitBox = await submit.boundingBox();
    expect(clearBox).not.toBeNull();
    expect(submitBox).not.toBeNull();
    expect(clearBox!.x + clearBox!.width <= submitBox!.x || submitBox!.x + submitBox!.width <= clearBox!.x).toBeTruthy();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
    await assertAxe(page);
    await page.screenshot({ path: "/tmp/phase114a-header-search-en-mobile.png", fullPage: true });
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/en");
    await page.locator("#site-search").fill("[DEMO] industrial technical equipment selection and maintenance guide");
    await page.screenshot({ path: "/tmp/phase114a-header-search-en-desktop.png", fullPage: true });
  });
});
