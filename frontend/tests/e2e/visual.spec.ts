import { expect, test } from "playwright/test";

const stableStates = [
  { name: "homepage", path: "/fa" },
  { name: "catalog", path: "/fa/shop" },
  { name: "pdp", path: "/fa/product/test-product" },
] as const;

test.describe("stable visual QA captures", () => {
  for (const state of stableStates) {
    test(`${state.name} desktop screenshot has meaningful output`, async ({ page }, testInfo) => {
      await page.setViewportSize({ width: 1280, height: 800 });
      await page.goto(state.path);
      await expect(page.locator("body")).toBeVisible();
      const screenshot = await page.screenshot({ animations: "disabled", caret: "hide" });
      await testInfo.attach(`${state.name}-desktop.png`, { body: screenshot, contentType: "image/png" });
      expect(screenshot.byteLength).toBeGreaterThan(1000);
    });

    test(`${state.name} mobile screenshot has meaningful output`, async ({ page }, testInfo) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto(state.path);
      await expect(page.locator("body")).toBeVisible();
      const screenshot = await page.screenshot({ animations: "disabled", caret: "hide", fullPage: true });
      await testInfo.attach(`${state.name}-mobile.png`, { body: screenshot, contentType: "image/png" });
      expect(screenshot.byteLength).toBeGreaterThan(1000);
    });
  }

  test("cart mobile screenshot has meaningful output", async ({ page }, testInfo) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/fa/cart");
    const screenshot = await page.screenshot({ animations: "disabled", caret: "hide", fullPage: true });
    await testInfo.attach("cart-mobile.png", { body: screenshot, contentType: "image/png" });
    expect(screenshot.byteLength).toBeGreaterThan(1000);
  });

  test("header desktop/mobile screenshots cover locale and search result", async ({ page }, testInfo) => {
    for (const state of [
      { name: "fa-desktop", path: "/fa", width: 1360, height: 900 },
      { name: "fa-mobile", path: "/fa", width: 390, height: 844 },
      { name: "en-desktop", path: "/en", width: 1360, height: 900 },
      { name: "en-mobile", path: "/en", width: 390, height: 844 },
    ]) {
      await page.setViewportSize({ width: state.width, height: state.height });
      await page.goto(state.path);
      const header = page.locator(".reference-header");
      await expect(header).toBeVisible();
      const screenshot = await header.screenshot({ animations: "disabled" });
      await testInfo.attach(`header-${state.name}.png`, { body: screenshot, contentType: "image/png" });
      expect(screenshot.byteLength).toBeGreaterThan(1000);
    }

    await page.setViewportSize({ width: 1360, height: 900 });
    await page.goto("/fa");
    await page.locator("#site-search").fill("DEMO-SKU-001");
    await page.locator("#site-search").press("Enter");
    await expect(page).toHaveURL(/\/fa\/shop\?q=DEMO-SKU-001/);
    const resultScreenshot = await page.locator(".reference-header").screenshot({ animations: "disabled" });
    await testInfo.attach("header-search-result.png", { body: resultScreenshot, contentType: "image/png" });
    expect(resultScreenshot.byteLength).toBeGreaterThan(1000);
  });
});
