import { describe, expect, it } from "vitest";
import { accountLocaleTag, formatAccountDate, formatAccountNumber } from "../lib/account-format";

describe("account and order presentation", () => {
  it("uses locale-aware number formatting", () => {
    expect(accountLocaleTag("en")).toBe("en-US");
    expect(formatAccountNumber("1234567", "en")).toContain("1,234,567");
    expect(formatAccountNumber("1234567", "fa")).toContain("۱٬۲۳۴٬۵۶۷");
  });

  it("formats dates without forcing Persian on English routes", () => {
    expect(formatAccountDate("2025-01-15T12:30:00Z", "en")).toMatch(/Jan/);
    expect(formatAccountDate("2025-01-15T12:30:00Z", "fa")).toMatch(/[۰-۹]/);
  });
});
