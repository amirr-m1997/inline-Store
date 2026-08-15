import { expect, test } from "playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("enterprise storefront critical flows", () => {
  test("homepage -> catalog -> product detail", async ({ page }) => {
    await page.goto("/fa");
    await expect(page.locator("main.enterprise-home")).toBeVisible();
    await page.getByRole("link", { name: /مشاهده همه/ }).first().click();
    await expect(page.locator("main.catalog-experience")).toBeVisible();
    const product = page.locator(".industrial-product-card a").first();
    await expect(product).toBeVisible();
    await product.click();
    await expect(page.locator("h1")).toBeVisible();
    await expect(page.locator("body")).toContainText(/SKU|کد/);
  });

  test("catalog search, filters and cursor navigation preserve URL state", async ({ page }) => {
    await page.goto("/fa/shop");
    const search = page.locator("#site-search");
    await search.fill("bearing");
    await search.press("Enter");
    await expect(page).toHaveURL(/q=bearing/);
    const filterButton = page.getByRole("button", { name: "فیلترها" });
    if (await filterButton.isVisible()) {
      await filterButton.click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await page.keyboard.press("Escape");
    }
    const next = page.getByRole("button", { name: /بعدی|صفحه بعد/ });
    if (await next.isVisible()) {
      await next.click();
      await expect(page).toHaveURL(/cursor=|page=/);
    }
  });

  test("variant selection and add-to-cart flow", async ({ page }) => {
    await page.goto("/fa/product/test-product");
    await expect(page).toHaveTitle("محصول تست");
    await expect(page.getByRole("heading", { level: 1, name: "محصول تست" })).toHaveCount(1);
    const variant = page.locator(".variant-selector button").first();
    if (await variant.count()) {
      await variant.focus();
      await expect(variant).toBeFocused();
      await variant.press("Enter");
      await expect(variant).toHaveAttribute("aria-pressed", "true");
    }
    const add = page.getByRole("button", { name: /افزودن به سبد|افزودن/ });
    if (await add.count()) await add.click();
  });

  test("login and cart checkout entry are reachable", async ({ page }) => {
    await page.goto("/fa/login");
    await expect(page.getByRole("heading").first()).toBeVisible();
    await page.goto("/fa/cart");
    await expect(page.locator("main")).toBeVisible();
    const checkout = page.getByRole("link", { name: /تسویه|پرداخت|ادامه/ });
    if (await checkout.count()) await expect(checkout.first()).toBeVisible();
  });

  test("critical storefront pages have no axe violations", async ({ page }) => {
    for (const path of ["/fa", "/fa/shop", "/fa/product/test-product", "/fa/login"]) {
      await page.goto(path);
      const results = await new AxeBuilder({ page }).disableRules(["color-contrast"]).analyze();
      expect(results.violations, `${path} accessibility violations`).toEqual([]);
    }
    await page.goto("/fa/shop");
    const filter = page.getByRole("button", { name: "فیلترها" });
    if (await filter.isVisible()) { await filter.click(); const drawer = page.getByRole("dialog"); await expect(drawer).toBeVisible(); const results = await new AxeBuilder({ page }).include('[role="dialog"]').disableRules(["color-contrast"]).analyze(); expect(results.violations).toEqual([]); }
  });
});
