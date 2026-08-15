import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const read = (file: string) => fs.readFileSync(path.resolve(process.cwd(), file), "utf8");

describe("authenticated account support center", () => {
  it("uses private noindex metadata and a locale-safe route", () => {
    const page = read("app/[locale]/account/support/page.tsx");
    expect(page).toContain("AccountSupportCenter");
    expect(page).toContain("index: false");
    expect(page).toContain("follow: false");
    expect(page).toContain("localizedAlternates");
    expect(page).toContain("/account/support");
  });

  it("loads only ownership-scoped histories and redirects unauthenticated users", () => {
    const source = read("components/account/account-support-center.tsx");
    expect(source).toContain("getProfile<Customer>()");
    expect(source).toContain("getSupportRequests<SupportRecord>()");
    expect(source).toContain("getWarrantyRegistrations<WarrantyRecord>()");
    expect(source).toContain("router.replace(`/${locale}/login`)");
    expect(source).not.toContain("customer_id");
    expect(source).not.toContain("internal_notes");
  });

  it("renders localized actions, statuses, separate empty/error states, and LTR references", () => {
    const source = read("components/account/account-support-center.tsx");
    for (const value of ["Support requests", "Warranty registration requests", "Submit request", "Register warranty request", "role=\"alert\"", "role=\"status\"", "dir=\"ltr\"", "account-support-empty", "Try again"]) expect(source).toContain(value);
    expect(source).toContain("requestTypes");
    expect(source).toContain("statuses");
  });

  it("exposes Support from the existing account navigation area", () => {
    const account = read("app/[locale]/account/page.tsx");
    expect(account).toContain("/${locale}/account/support");
    expect(account).toContain("locale === \"en\" ? \"Support\" : \"پشتیبانی\"");
  });

  it("normalizes profile fields before binding them to controlled inputs", () => {
    const account = read("app/[locale]/account/page.tsx");
    expect(account).toContain("function normalizeProfile");
    expect(account).toContain("setProfile(normalizeProfile(value))");
    expect(account).toContain("setProfile(normalizeProfile(await updateProfile<Customer>(profile)))");
    expect(account).toContain('email: value.email ?? ""');
    expect(account).toContain('address: value.address ?? ""');
    expect(account).toContain('customer_type: value.customer_type === "business" ? "business" : "personal"');
  });
});
