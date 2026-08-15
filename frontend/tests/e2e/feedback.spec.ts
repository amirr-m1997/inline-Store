import { expect, test } from "playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("customer feedback", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/v1/site/support/feedback/**", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ id: 9001 }),
        });
      } else {
        await route.continue();
      }
    });
  });

  for (const locale of ["fa", "en"]) {
    test(`${locale} feedback form submits and exposes an accessible success state`, async ({ page }, testInfo) => {
      let submittedPayload: Record<string, unknown> | undefined;
      page.on("request", request => {
        if (request.url().includes("/api/v1/site/support/feedback") && request.method() === "POST") submittedPayload = request.postDataJSON();
      });
      await page.goto(`/${locale}/support/feedback`);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
      await expect(page.getByLabel(locale === "fa" ? "نوع بازخورد" : "Feedback type")).toBeVisible();
      await page.getByLabel(locale === "fa" ? "پیام *" : "Message *").fill("A deterministic browser feedback message");
      await page.locator("#feedback-rating-4").check();
      const viewportName = testInfo.project.name === "mobile-chromium" ? "390" : "1440";
      await page.screenshot({ path: `/tmp/phase109b-feedback-${locale}-${viewportName}.png`, fullPage: true });
      if (locale === "fa") await page.screenshot({ path: "/tmp/phase109b-feedback-fa-rating-4.png", fullPage: true });

      const results = await new AxeBuilder({ page }).analyze();
      expect(results.violations, `${locale} feedback accessibility violations`).toEqual([]);

      await page.getByRole("button", { name: locale === "fa" ? "ارسال بازخورد" : "Submit Feedback" }).click();
      await expect.poll(() => submittedPayload?.rating).toBe(4);
      await expect(page.getByRole("status")).toBeVisible();
      await expect(page.getByRole("status")).toContainText(locale === "fa" ? "بازخورد شما دریافت شد" : "Your feedback was received");
    });
  }

  test("fa feedback tablet layout screenshot", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "chromium", "Tablet capture is covered by the desktop browser project.");
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto("/fa/support/feedback");
    await page.locator("#feedback-rating-4").check();
    await page.screenshot({ path: "/tmp/phase109b-feedback-fa-768.png", fullPage: true });
  });
});
