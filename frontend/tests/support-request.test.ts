import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const read = (file:string) => fs.readFileSync(path.resolve(process.cwd(), file), "utf8");

describe("Phase 10.4 support request experience", () => {
  it("renders the localized route with noindex metadata", () => {
    const page = read("app/[locale]/support/request/page.tsx");
    expect(page).toContain("SupportRequestForm");
    expect(page).toContain("robots:{index:false,follow:true}");
    expect(page).toContain("localizedAlternates");
    expect(page).toContain("canonical");
    expect(page).toContain("support/request");
    expect(page).toContain("<h1>");
  });

  it("covers supported request choices, labels, validation and success/error semantics", () => {
    const source = read("components/content/support-request-form.tsx");
    for (const value of ["complaint", "product_support", "order_support", "warranty", "sales", "other"]) expect(source).toContain(value);
    for (const label of ["full_name", "phone", "email", "subject", "message"]) expect(source).toContain(label);
    expect(source).toContain("required");
    expect(source).toContain('role="alert"');
    expect(source).toContain('role="status"');
    expect(source).toContain("reference");
    expect(source).toContain('dir="ltr"');
    expect(source).toContain("Your support request was received");
    expect(source).not.toContain("response time");
    expect(source).not.toContain("internal_notes");
    expect(source).not.toContain("customer.id");
  });

  it("renders owned history fields and an intentional empty state", () => {
    const source = read("components/content/support-request-form.tsx");
    for (const field of ["reference", "request_type", "status", "subject", "submitted_at"]) expect(source).toContain(field);
    expect(source).toContain("getSupportRequests");
    expect(source).toContain("history?.length");
    expect(source).toContain("catch(() => setHistory([]))");
  });

  it("resolves product/order context only through backend APIs", () => {
    const source = read("components/content/support-request-form.tsx");
    expect(source).toContain("getProduct");
    expect(source).toContain("getOrder");
    expect(source).toContain("product: product.id");
    expect(source).toContain("order: order.id");
  });
});
