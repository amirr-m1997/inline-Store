import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const read = (file: string) => fs.readFileSync(path.resolve(process.cwd(), file), "utf8");

describe("Phase 12.2 customer RFQ UI", () => {
  it("defines localized noindex public and private routes", () => {
    const publicPage = read("app/[locale]/rfq/page.tsx");
    const history = read("app/[locale]/account/rfq/page.tsx");
    expect(publicPage).toContain('robots: { index: false, follow: true }');
    expect(history).toContain('robots: { index: false, follow: false }');
    expect(publicPage).toContain("localizedAlternates");
  });

  it("adds a PDP CTA without changing cart behavior", () => {
    const page = read("app/[locale]/product/[slug]/page.tsx");
    expect(page).toContain("/${locale}/rfq?product=");
    expect(page).toContain("Request a Quote");
    expect(page).toContain("استعلام قیمت");
    expect(page).toContain("ProductDetailInteractive");
  });

  it("resolves trusted product context and never accepts a price field", () => {
    const source = read("components/rfq/rfq-form.tsx");
    expect(source).toContain("getProduct(slug)");
    expect(source).toContain("product: line.product.id");
    expect(source).toContain("requested_quantity");
    expect(source).not.toContain("price:");
    expect(source).not.toContain("discount");
  });

  it("supports trusted cart context, bounded multi-item editing, and independent quantities", () => {
    const source = read("components/rfq/rfq-form.tsx");
    expect(source).toContain("getRfqCartContext()");
    expect(source).toContain('params.get("source")');
    expect(source).toContain("lines.length >= 25");
    expect(source).toContain("Remove item");
    expect(source).toContain("Requested quantity for");
    expect(source).toContain("Quotation Request Items");
  });

  it("exposes an explicit cart-to-RFQ action without checkout mutation", () => {
    const source = read("app/[locale]/cart/page.tsx");
    expect(source).toContain("/rfq?source=cart");
    expect(source).toContain("Request a Quote for Cart Items");
  });

  it("covers accessible form states and duplicate-item prevention", () => {
    const source = read("components/rfq/rfq-form.tsx");
    for (const value of ["role=\"alert\"", "role=\"status\"", "Contact name *", "Requested quantity", "Remove item", "This product is already in the request.", "Submitting…"]) expect(source).toContain(value);
  });

  it("renders backend reference/status and explicitly separates RFQ from quotation/order", () => {
    const source = read("components/rfq/rfq-form.tsx");
    expect(source).toContain("success.reference");
    expect(source).toContain("success.status");
    expect(source).toContain("does not constitute a quotation or an order");
    expect(source).not.toContain("final_price");
  });

  it("provides ownership-scoped account history/detail without internal fields", () => {
    const source = read("components/account/account-rfq.tsx");
    expect(source).toContain("getRfqs()");
    expect(source).toContain("getRfq(reference)");
    expect(source).toContain("/account/rfq/");
    expect(source).not.toContain("internal_notes");
    expect(source).toContain("localizedStatus");
  });

  it("exposes RFQ in account navigation but not the crowded primary header", () => {
    const account = read("app/[locale]/account/page.tsx");
    const header = read("components/layout/main-header.tsx");
    expect(account).toContain("/${locale}/account/rfq");
    expect(account).toContain("استعلام‌های قیمت");
    expect(header).not.toContain("/rfq");
  });
});
