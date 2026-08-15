import { expect, test, type Page } from "playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function assertClean(page: Page) {
  const result = await new AxeBuilder({ page }).analyze();
  expect(result.violations).toEqual([]);
}

test.describe("Phase 12.2 RFQ customer flow", () => {
  test("PDP opens a trusted product RFQ and submits without quotation claims", async ({ page }, testInfo) => {
    await page.goto("/fa/product/test-product");
    await page.locator('a[href="/fa/rfq?product=test-product"]').click();
    await expect(page).toHaveURL(/\/fa\/rfq\?product=test-product/);
    await expect(page.getByRole("heading", { level: 1, name: "استعلام قیمت" })).toBeVisible();
    await expect(page.locator(".rfq-item")).toContainText("محصول تست");
    await page.getByLabel("نام تماس *").fill("خریدار نمونه");
    await page.getByLabel("تلفن *", { exact: true }).fill("09121234567");
    await page.getByLabel("شرح نیاز").fill("درخواست بررسی قیمت برای یک پروژه نمونه");
    await page.getByRole("button", { name: "ثبت استعلام قیمت" }).click();
    await expect(page.getByRole("heading", { name: "درخواست استعلام قیمت شما ثبت شد." })).toBeVisible();
    await expect(page.locator(".rfq-reference code")).toHaveText("RFQ-DEMO1234");
    await expect(page.locator(".rfq-success")).not.toContainText("ریال");
    await expect(page.locator(".rfq-success")).not.toContainText("تومان");
    await assertClean(page);
    await page.screenshot({ path: testInfo.project.name === "mobile-chromium" ? "/tmp/phase122-rfq-success-fa.png" : "/tmp/phase122-rfq-success-fa.png", fullPage: true });
  });

  test("RFQ form remains usable in English and dark theme", async ({ page }, testInfo) => {
    await page.goto("/en/rfq?product=test-product");
    await expect(page.getByRole("heading", { level: 1, name: "Request for Quotation" })).toBeVisible();
    await expect(page.getByLabel("Requested quantity")).toBeVisible();
    await assertClean(page);
    await page.screenshot({ path: "/tmp/phase122-rfq-en-desktop.png", fullPage: true });
    await page.evaluate(() => window.localStorage.setItem("theme", "dark"));
    await page.reload();
    await expect(page.locator("html")).toHaveClass(/dark/);
    await assertClean(page);
    await page.screenshot({ path: "/tmp/phase122-rfq-dark.png", fullPage: true });
    await page.goto("/fa/rfq?product=test-product");
    await page.screenshot({ path: testInfo.project.name === "mobile-chromium" ? "/tmp/phase122-rfq-fa-mobile.png" : "/tmp/phase122-rfq-fa-desktop.png", fullPage: true });
  });
});
