import { expect, test } from "playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function assertClean(page: import("playwright/test").Page) {
  const result = await new AxeBuilder({ page }).analyze();
  expect(result.violations).toEqual([]);
}

test.describe("Phase 12.6 multi-product RFQ", () => {
  test("PDP RFQ can add a second trusted product and submit one request", async ({ page }, testInfo) => {
    await page.goto("/fa/rfq?product=test-product");
    await expect(page.locator(".rfq-item")).toContainText("محصول تست");
    await page.getByLabel("افزودن محصول دیگر").fill("محصول دوم");
    await page.getByRole("button", { name: "جستجو", exact: true }).click();
    await page.getByRole("button", { name: /محصول دوم/ }).click();
    await expect(page.locator(".rfq-item")).toHaveCount(2);
    await page.getByLabel("تعداد درخواستی محصول تست").fill("2");
    await page.getByLabel("تعداد درخواستی محصول دوم").fill("5");
    await page.getByLabel("نام تماس *").fill("خریدار چندقلمی");
    await page.getByLabel("تلفن *", { exact: true }).fill("09121234567");
    await page.getByRole("button", { name: "ثبت استعلام قیمت" }).click();
    await expect(page.getByRole("heading", { name: "درخواست استعلام قیمت شما ثبت شد." })).toBeVisible();
    await expect(page.locator(".rfq-success-items")).toContainText("محصول تست");
    await expect(page.locator(".rfq-success-items")).toContainText("محصول دوم");
    await assertClean(page);
    await page.screenshot({ path: testInfo.project.name === "mobile-chromium" ? "/tmp/phase126-rfq-multi-fa-mobile.png" : "/tmp/phase126-rfq-multi-fa-desktop.png", fullPage: true });
    await page.screenshot({ path: "/tmp/phase126-rfq-multi-success.png", fullPage: true });
  });

  test("Cart-to-RFQ keeps the original cart and quantities", async ({ page }) => {
    await page.goto("/fa/cart");
    await expect(page.locator(".cart-item")).toHaveCount(2);
    await page.getByRole("link", { name: "استعلام قیمت اقلام سبد" }).click();
    await expect(page).toHaveURL(/\/fa\/rfq\?source=cart/);
    await expect(page.locator(".rfq-item")).toHaveCount(2);
    await expect(page.getByLabel("تعداد درخواستی محصول تست")).toHaveValue("2");
    await expect(page.getByLabel("تعداد درخواستی محصول دوم")).toHaveValue("3");
    await page.getByLabel("تعداد درخواستی محصول تست").fill("7");
    await page.getByLabel("نام تماس *").fill("خریدار سبد");
    await page.getByLabel("تلفن *", { exact: true }).fill("09121234567");
    await page.getByRole("button", { name: "ثبت استعلام قیمت" }).click();
    await expect(page.locator(".rfq-success-items")).toContainText("محصول دوم");
    await assertClean(page);
    await page.screenshot({ path: "/tmp/phase126-cart-rfq-fa.png", fullPage: true });
    await page.goto("/fa/cart");
    await expect(page.locator(".cart-item")).toHaveCount(2);
    await expect(page.locator(".cart-item-controls").first()).toContainText("۲");
    await expect(page.locator(".cart-item-controls").nth(1)).toContainText("۳");
  });

  test("English and dark multi-item RFQ surfaces remain readable", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "chromium", "Representative language screenshots are captured on desktop only.");
    await page.goto("/en/rfq?product=test-product");
    await expect(page.getByRole("heading", { level: 1, name: "Request for Quotation" })).toBeVisible();
    await assertClean(page);
    await page.screenshot({ path: "/tmp/phase126-rfq-multi-en.png", fullPage: true });
    await page.evaluate(() => window.localStorage.setItem("theme", "dark"));
    await page.reload();
    await expect(page.locator("html")).toHaveClass(/dark/);
    await assertClean(page);
    await page.screenshot({ path: "/tmp/phase126-rfq-multi-dark.png", fullPage: true });
  });
});
