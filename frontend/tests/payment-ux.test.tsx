import { describe, expect, it } from "vitest";
import { paymentGatewayLabel, paymentState } from "../lib/payment-presenters";

describe("payment UX state mapping", () => {
  it("keeps the real gateway context and mock disclosure label", () => {
    expect(paymentGatewayLabel("mock_zarinpal")).toBe("زرین‌پال");
    expect(paymentGatewayLabel("zarinpal")).toBe("زرین‌پال");
    expect(paymentGatewayLabel()).toBe("درگاه پرداخت");
  });

  it.each([
    ["verified", "success"], ["failed", "failed"], ["cancelled", "cancelled"],
    ["created", "pending"], ["pending", "pending"], ["gateway_unknown", "unknown"],
  ] as const)("maps backend status %s to visible state %s", (status, expected) => {
    expect(paymentState(status)).toBe(expected);
  });
});
