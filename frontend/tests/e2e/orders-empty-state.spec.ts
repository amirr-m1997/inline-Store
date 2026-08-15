import { expect, test } from "playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function mockEmptyOrders(page: import("playwright").Page) {
  await page.route("**/api/customer/orders/**", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: "[]",
  }));
}

async function mockOrders(page: import("playwright").Page) {
  await page.route("**/api/customer/orders/**", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify([
      { id: 101, order_number: "ORD-2026-0000000001", status_label: "در حال بررسی", created_at: "2026-08-15T09:30:00Z", final_amount: "1250000", items_count: 2 },
      { id: 102, order_number: "ORD-2026-0000000002", status_label: "تکمیل‌شده", created_at: "2026-08-14T09:30:00Z", final_amount: "2750000", items_count: 4 },
    ]),
  }));
}

function doesNotIntersect(first: DOMRect, second: DOMRect) {
  return first.right <= second.left || second.right <= first.left || first.bottom <= second.top || second.bottom <= first.top;
}

test.describe("Account orders empty-state layout", () => {
  test("keeps the empty-state copy and CTA separated inside the account content", async ({ page }, testInfo) => {
    await mockEmptyOrders(page);
    await page.goto("/fa/account/orders");
    await expect(page.getByRole("heading", { level: 1, name: "سفارش‌های من" })).toBeVisible();
    await expect(page.getByRole("heading", { level: 2, name: "سفارشی ثبت نشده است" })).toBeVisible();

    const geometry = await page.locator(".orders-empty-state").evaluate((container) => {
      const description = container.querySelector(".orders-empty-description");
      const cta = container.querySelector(".orders-empty-cta");
      if (!description || !cta) throw new Error("Orders empty-state elements are missing");
      const containerRect = container.getBoundingClientRect();
      const descriptionRect = description.getBoundingClientRect();
      const ctaRect = cta.getBoundingClientRect();
      return {
        container: { left: containerRect.left, right: containerRect.right, top: containerRect.top, bottom: containerRect.bottom },
        description: { left: descriptionRect.left, right: descriptionRect.right, top: descriptionRect.top, bottom: descriptionRect.bottom },
        cta: { left: ctaRect.left, right: ctaRect.right, top: ctaRect.top, bottom: ctaRect.bottom },
      };
    });
    expect(doesNotIntersect(geometry.description as DOMRect, geometry.cta as DOMRect)).toBeTruthy();
    for (const child of [geometry.description, geometry.cta]) {
      expect(child.left).toBeGreaterThanOrEqual(geometry.container.left);
      expect(child.right).toBeLessThanOrEqual(geometry.container.right);
      expect(child.top).toBeGreaterThanOrEqual(geometry.container.top);
      expect(child.bottom).toBeLessThanOrEqual(geometry.container.bottom);
    }
    expect(await page.locator("h1").count()).toBe(1);
    await expect(new AxeBuilder({ page }).include(".customer-orders-page").analyze()).resolves.toMatchObject({ violations: [] });

    const screenshotPath = testInfo.project.name === "mobile-chromium"
      ? "/tmp/orders-empty-fa-mobile.png"
      : "/tmp/orders-empty-fa-desktop.png";
    await page.screenshot({ path: screenshotPath, fullPage: true });
  });

  test("renders the English empty state without changing its flow layout", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name === "mobile-chromium", "English representative screenshot is desktop-only");
    await mockEmptyOrders(page);
    await page.goto("/en/account/orders");
    await expect(page.getByRole("heading", { level: 1, name: "My orders" })).toBeVisible();
    await expect(page.getByRole("heading", { level: 2, name: "No orders yet" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Go to shop" })).toBeVisible();
    await page.screenshot({ path: "/tmp/orders-empty-en-desktop.png", fullPage: true });
  });

  test("keeps the empty state readable in dark theme", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name === "mobile-chromium", "Dark representative screenshot is desktop-only");
    await page.addInitScript(() => localStorage.setItem("theme", "dark"));
    await mockEmptyOrders(page);
    await page.goto("/fa/account/orders");
    await expect(page.locator("html.dark .orders-empty-state")).toBeVisible();
    await page.screenshot({ path: "/tmp/orders-empty-dark.png", fullPage: true });
  });

  test("preserves the populated order-card presentation", async ({ page }) => {
    await mockOrders(page);
    await page.goto("/fa/account/orders");
    await expect(page.locator(".customer-order-card")).toHaveCount(2);
    await expect(page.getByText("ORD-2026-0000000001")).toBeVisible();
    await expect(page.getByText("ORD-2026-0000000002")).toBeVisible();
    await expect(page.getByText("تکمیل‌شده")).toBeVisible();
    await expect(page.locator(".customer-order-card").first()).toHaveAttribute("href", "/fa/account/orders/101");
  });
});
