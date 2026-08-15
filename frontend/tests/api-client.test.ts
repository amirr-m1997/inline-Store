import { afterEach, describe, expect, it, vi } from "vitest";
import { apiRequest, ApiError } from "../lib/api/client";

describe("API error messages", () => {
  afterEach(() => vi.restoreAllMocks());

  it("surfaces nested field validation messages instead of the generic fallback", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      customer_email: ["این ایمیل قبلاً ثبت شده است."],
      shipping_postal_code: ["کد پستی معتبر نیست."],
    }), { status: 400, headers: { "Content-Type": "application/json" } })));

    await expect(apiRequest("/api/v1/cart/", { method: "PATCH", body: { customer: {} } }))
      .rejects.toMatchObject({ status: 400, message: "این ایمیل قبلاً ثبت شده است. کد پستی معتبر نیست." } satisfies Partial<ApiError>);
  });
});
