import { expect, test } from "playwright/test";

test.describe("CompanyInfo homepage hero carousel", () => {
  test("renders the first slide, supports keyboard navigation, and captures responsive states", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/fa");
    const hero = page.locator(".site-hero");
    await expect(hero).toBeVisible();
    await expect(hero.locator("h1")).toHaveText("بنر اول");
    await expect(hero.locator(".site-hero-control-next")).toHaveAccessibleName("بنر بعدی");
    await hero.focus();
    await page.keyboard.press("ArrowLeft");
    await expect(hero.locator("h1")).toHaveText("بنر دوم");
    await page.screenshot({ path: "/tmp/phase127-home-fa-desktop.png", animations: "disabled" });

    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/fa");
    await expect(page.locator(".site-hero h1")).toHaveText("بنر اول");
    await page.waitForTimeout(300);
    await page.screenshot({ path: "/tmp/phase127-home-fa-mobile.png", animations: "disabled", fullPage: true });

    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/en");
    await expect(page.locator(".site-hero h1")).toBeVisible();
    await page.screenshot({ path: "/tmp/phase127-home-en-desktop.png", animations: "disabled" });
    await page.getByRole("button", { name: "تغییر تم" }).click();
    await expect(page.locator("html")).toHaveClass(/dark/);
    await page.screenshot({ path: "/tmp/phase127-home-dark.png", animations: "disabled" });
  });
});
