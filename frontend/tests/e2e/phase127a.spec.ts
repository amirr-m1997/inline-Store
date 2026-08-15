import { expect, test } from "playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function assertKnowledgeStartsBelowHeader(page: import("playwright").Page, path: string) {
  await page.goto(path);
  await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible();
  await page.waitForFunction(() => getComputedStyle(document.documentElement).getPropertyValue("--site-header-height").trim() !== "0px");
  const header = await page.locator(".reference-header").boundingBox();
  const heading = await page.getByRole("heading", { level: 1 }).first().boundingBox();
  expect(header).not.toBeNull();
  expect(heading).not.toBeNull();
  expect(heading!.y).toBeGreaterThanOrEqual(header!.y + header!.height - 1);
}

test.describe("Phase 12.7A Knowledge Center compact layout", () => {
  test("H1 remains below the measured sticky header for all locale/filter entry states", async ({ page }) => {
    for (const path of ["/fa/knowledge", "/fa/knowledge?type=event", "/en/knowledge", "/en/knowledge?type=event"]) {
      await assertKnowledgeStartsBelowHeader(page, path);
    }
  });

  test("the measured offset remains safe across the supported viewport matrix", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "chromium", "The mobile project has a dedicated responsive assertion.");
    for (const viewport of [[360, 800], [390, 844], [768, 1024], [1024, 768], [1280, 800], [1440, 900]]) {
      await page.setViewportSize({ width: viewport[0], height: viewport[1] });
      await assertKnowledgeStartsBelowHeader(page, "/fa/knowledge");
      await assertKnowledgeStartsBelowHeader(page, "/fa/knowledge?type=event");
    }
  });

  test("all Knowledge content-type filters remain URL-addressable and compact", async ({ page }) => {
    await page.goto("/fa/knowledge");
    for (const [label, value] of [["اخبار", "news"], ["رویدادها", "event"], ["مقالات فنی", "technical_article"], ["راهنمای محصول", "product_guide"], ["راهنمای انتخاب", "buying_guide"], ["معرفی محصول", "product_announcement"]] as const) {
      await expect(page.getByRole("link", { name: label, exact: true })).toHaveAttribute("href", `/fa/knowledge?type=${value}`);
    }
    await expect(page.getByRole("link", { name: "جست‌وجو در سایت" })).toHaveAttribute("href", "/fa/search");
    await expect(page.locator(".site-search-form")).toHaveCount(0);
  });

  test("desktop Persian, event-filtered, English, and dark surfaces remain axe-clean", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "chromium", "Representative desktop screenshots are captured once.");
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/fa/knowledge");
    await expect(new AxeBuilder({ page }).analyze()).resolves.toMatchObject({ violations: [] });
    await page.screenshot({ path: "/tmp/phase127a-knowledge-fa-desktop.png", fullPage: true });
    await page.goto("/fa/knowledge?type=event");
    await expect(new AxeBuilder({ page }).analyze()).resolves.toMatchObject({ violations: [] });
    await page.screenshot({ path: "/tmp/phase127a-knowledge-fa-event-desktop.png", fullPage: true });
    await page.goto("/en/knowledge");
    await expect(page.locator("html")).toHaveAttribute("dir", "ltr");
    await expect(new AxeBuilder({ page }).analyze()).resolves.toMatchObject({ violations: [] });
    await page.screenshot({ path: "/tmp/phase127a-knowledge-en-desktop.png", fullPage: true });
    await page.evaluate(() => localStorage.setItem("theme", "dark"));
    await page.reload();
    await expect(page.locator("html")).toHaveClass(/dark/);
    await expect(new AxeBuilder({ page }).analyze()).resolves.toMatchObject({ violations: [] });
    await page.screenshot({ path: "/tmp/phase127a-knowledge-dark.png", fullPage: true });
  });

  test("mobile Knowledge layout has no overflow and preserves the header offset", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "mobile-chromium", "Mobile screenshot is captured on the mobile Chromium project.");
    await page.setViewportSize({ width: 390, height: 844 });
    await assertKnowledgeStartsBelowHeader(page, "/fa/knowledge");
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    expect(await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth)).toBe(false);
    await page.screenshot({ path: "/tmp/phase127a-knowledge-fa-mobile.png", fullPage: true });
  });
});
