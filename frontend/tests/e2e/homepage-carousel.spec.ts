import { expect, test } from "playwright/test";

test.describe("CompanyInfo homepage hero carousel", () => {
  test("renders the first slide, supports keyboard navigation, and captures responsive states", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/fa");
    const hero = page.locator(".site-hero");
    await expect(hero).toBeVisible();
    await expect(hero.locator("h1")).toHaveText("بنر اول");
    await expect(hero.locator(".site-hero-media")).toBeVisible();
    await expect(hero.locator(".site-hero-control-next")).toHaveAccessibleName("بنر بعدی");
    await hero.focus();
    await page.keyboard.press("ArrowLeft");
    await expect(hero.locator("h1")).toHaveText("بنر دوم");
    await page.screenshot({ path: "/tmp/phase127-home-fa-desktop.png", animations: "disabled" });

    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/fa");
    await expect(page.locator(".site-hero h1")).toHaveText("بنر اول");
    const singleBannerImage = page.locator(".site-hero-media--single");
    await expect(page.locator(".site-hero img")).toHaveCount(1);
    await expect(singleBannerImage).toBeVisible();
    await expect.poll(() => singleBannerImage.evaluate((image: HTMLImageElement) => image.naturalWidth)).toBeGreaterThan(0);
    await expect.poll(async () => {
      const heroBounds = await page.locator(".site-hero").boundingBox();
      const imageBounds = await singleBannerImage.boundingBox();
      const dimensions = await singleBannerImage.evaluate((image: HTMLImageElement) => ({ width: image.naturalWidth, height: image.naturalHeight }));
      return heroBounds && imageBounds && Math.abs(imageBounds.width - heroBounds.width) < 3
        && Math.abs(imageBounds.height / imageBounds.width - dimensions.height / dimensions.width) < 0.01
        && imageBounds.y + imageBounds.height <= heroBounds.y + heroBounds.height;
    }).toBe(true);
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
