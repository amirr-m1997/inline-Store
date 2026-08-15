import { expect, test } from "playwright/test";

function installConsoleGuards(page: import("playwright").Page) {
  const unauthorized: string[] = [];
  const controlledWarnings: string[] = [];
  const runtimeErrors: string[] = [];
  page.on("response", (response) => {
    if (response.status() === 401) unauthorized.push(`${response.request().method()} ${response.url()}`);
  });
  page.on("console", (message) => {
    if (/uncontrolled|controlled input/i.test(message.text())) controlledWarnings.push(`${message.type()}: ${message.text()}`);
  });
  page.on("pageerror", (error) => runtimeErrors.push(error.message));
  return { unauthorized, controlledWarnings, runtimeErrors };
}

async function expectClean(page: import("playwright").Page, path: string) {
  const guards = installConsoleGuards(page);
  await page.goto(path);
  await page.waitForTimeout(300);
  expect(guards.unauthorized, `Unexpected 401 while loading ${path}`).toEqual([]);
  expect(guards.controlledWarnings, `Controlled input warning while loading ${path}`).toEqual([]);
  expect(guards.runtimeErrors, `Runtime error while loading ${path}`).toEqual([]);
}

test.describe("Phase 12.7B console regressions", () => {
  test("public Knowledge, Search, RFQ, warranty, and support routes remain console-clean", async ({ page }) => {
    for (const path of [
      "/fa/knowledge",
      "/fa/knowledge?type=event",
      "/fa/search?q=پیچ",
      "/en/knowledge",
      "/en/search?q=test",
      "/fa/rfq",
      "/en/rfq",
      "/fa/support/warranty",
      "/en/support/warranty",
      "/fa/support/request",
    ]) await expectClean(page, path);
  });

  test("cart customer fields remain controlled when optional API fields are absent", async ({ page }) => {
    await expectClean(page, "/fa/cart");
    await expect(page.locator("input").first()).toBeVisible();
  });

  test("saving customer information does not return a cart PATCH 500", async ({ page }) => {
    const cartPatchStatuses: number[] = [];
    page.on("response", (response) => {
      if (response.request().method() === "PATCH" && response.url().includes("/api/v1/cart/")) cartPatchStatuses.push(response.status());
    });
    await page.goto("/fa/cart");
    await page.getByLabel("نام *").fill("خریدار تست");
    await page.getByLabel("نام خانوادگی *").fill("سبد خرید");
    await page.getByLabel("شماره تماس *").fill("09121234567");
    await page.getByLabel("استان *").fill("تهران");
    await page.getByLabel("شهر *").fill("تهران");
    await page.getByLabel("کد پستی *").fill("1234567890");
    await page.getByLabel("نشانی کامل *").fill("نشانی تست");
    await page.getByRole("button", { name: "ذخیره اطلاعات مشتری" }).click();
    await expect(page.getByRole("status")).toContainText("ذخیره شد");
    expect(cartPatchStatuses).toEqual([200]);
  });

  test("typing and async context updates do not emit controlled-input warnings", async ({ page }) => {
    const guards = installConsoleGuards(page);
    const search = page.locator(".reference-search-input");
    await page.goto("/fa/knowledge");
    await search.fill("پیچ");
    await page.getByRole("button", { name: "پاک کردن جست‌وجو" }).click();
    await search.fill("دوباره");
    await search.press("Enter");
    await page.waitForTimeout(250);

    await page.goto("/fa/rfq");
    await page.getByLabel("نام تماس *").fill("مشتری تست");
    await page.getByLabel("تلفن *").fill("09121234567");
    await page.getByLabel("افزودن محصول دیگر").fill("محصول");
    await page.getByRole("button", { name: "جستجو" }).click();
    await page.waitForTimeout(250);

    await page.goto("/fa/cart");
    await page.getByRole("link", { name: "استعلام قیمت اقلام سبد" }).click();
    await page.waitForTimeout(350);

    expect(guards.controlledWarnings, "Controlled-input warning during interaction").toEqual([]);
    expect(guards.runtimeErrors, "Runtime error during interaction").toEqual([]);
  });
});
