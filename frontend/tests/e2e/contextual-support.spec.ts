import { expect, test } from "playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("contextual product support", () => {
  test("Customer Service Hub links use the implemented localized routes", async ({ page }) => {
    for (const locale of ["fa", "en"]) {
      await page.goto(`/${locale}/support`);
      const links = page.locator("a");
      await expect(links.filter({ hasText: locale === "fa" ? "گارانتی" : "Warranty" })).toHaveAttribute("href", `/${locale}/support/warranty`);
      await expect(links.filter({ hasText: locale === "fa" ? "ثبت درخواست" : "Support request" })).toHaveAttribute("href", `/${locale}/support/request`);
      await expect(links.filter({ hasText: locale === "fa" ? "بازخورد" : "Feedback" })).toHaveAttribute("href", `/${locale}/support/feedback`);
      await expect(links.filter({ hasText: locale === "fa" ? "منابع فنی" : "Technical resources" })).toHaveAttribute("href", `/${locale}/resources`);
      await expect(page.locator(`a[href="/${locale}/support/resources"]`)).toHaveCount(0);
    }
  });

  test("public customer service pages remain axe-clean", async ({ page }, testInfo) => {
    for (const path of ["/fa/support", "/fa/support/warranty", "/fa/support/request", "/fa/support/feedback", "/en/support", "/en/support/warranty", "/en/support/request", "/en/support/feedback"]) {
      await page.goto(path);
      if (["/fa/support/warranty", "/fa/support/request", "/en/support/warranty", "/en/support/request"].includes(path)) {
        const viewport = testInfo.project.name === "mobile-chromium" ? "mobile" : "desktop";
        const locale = path.startsWith("/en/") ? "en" : "fa";
        const pageName = path.includes("warranty") ? "warranty" : "request";
        await page.screenshot({ path: `/tmp/phase109a-${pageName}-${locale}-${viewport}.png`, fullPage: true });
        expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(await page.evaluate(() => innerWidth));
      }
      if (path === "/fa/support") {
        const viewport = testInfo.project.name === "mobile-chromium" ? "mobile" : "desktop";
        await page.screenshot({ path: `/tmp/phase108-final-support-fa-${viewport}.png`, fullPage: true });
      }
      await expect(page.locator("h1")).toHaveCount(1);
      const results = await new AxeBuilder({ page }).disableRules(["color-contrast"]).analyze();
      expect(results.violations, path).toEqual([]);
    }
  });

  test("PDP exposes safe product support and warranty context", async ({ page }) => {
    await page.goto("/fa/product/test-product");
    const support = page.getByRole("link", { name: "پشتیبانی محصول" });
    const warranty = page.getByRole("link", { name: "اطلاعات گارانتی" });
    await expect(support).toHaveAttribute("href", "/fa/support/request?product=test-product");
    await expect(warranty).toHaveAttribute("href", "/fa/support/warranty?product=test-product");
    await support.click();
    await expect(page.getByRole("heading", { name: "موضوع درخواست" })).toBeVisible();
    await expect(page.locator(".support-context")).toContainText("محصول تست");
    const results = await new AxeBuilder({ page }).disableRules(["color-contrast"]).analyze();
    expect(results.violations).toEqual([]);
  });
});
