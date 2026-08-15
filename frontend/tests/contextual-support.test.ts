import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const read = (file: string) => fs.readFileSync(path.resolve(process.cwd(), file), "utf8");

describe("Phase 10.7 contextual support", () => {
  it("keeps Customer Service technical resources on the existing resources route", () => {
    const source = read("app/[locale]/support/page.tsx");
    expect(source).toContain("path===\"resources\"?`/${locale}/resources`");
    expect(source).not.toContain("/support/resources");
  });

  it("adds locale-safe secondary PDP support and warranty links", () => {
    const source = read("app/[locale]/product/[slug]/page.tsx");
    expect(source).toContain("/support/request?product=");
    expect(source).toContain("/support/warranty?product=");
    expect(source).toContain("encodeURIComponent(product.slug)");
  });

  it("adds order support without changing order data or ownership flow", () => {
    const source = read("app/[locale]/account/orders/[orderId]/page.tsx");
    expect(source).toContain("/support/request?order=");
    expect(source).toContain("encodeURIComponent(order.id)");
    expect(source).toContain("Request support for this order");
  });

  it("resolves public product context and authenticated order context before submission", () => {
    const source = read("components/content/support-request-form.tsx");
    expect(source).toContain("getProduct(productSlug)");
    expect(source).toContain("getOrder<OrderContext>(orderId)");
    expect(source).toContain("product: product.id");
    expect(source).toContain("order: order.id");
    expect(source).toContain("selected context is unavailable");
    expect(source).toContain("dir=\"ltr\"");
  });

  it("associates trusted product context with warranty registration", () => {
    const source = read("components/content/warranty-registration-form.tsx");
    expect(source).toContain("getProduct(slug)");
    expect(source).toContain("product: product.id");
    expect(source).toContain("Product context");
  });
});
