export type PaymentState = "success" | "failed" | "cancelled" | "pending" | "unknown";

export function paymentGatewayLabel(gateway?: string) {
  if (!gateway) return "درگاه پرداخت";
  if (gateway.includes("zarinpal")) return "زرین‌پال";
  return gateway;
}

export function paymentState(status: string): PaymentState {
  if (status === "verified" || ["paid", "success", "succeeded"].includes(status)) return "success";
  if (["failed", "error"].includes(status)) return "failed";
  if (["cancelled", "canceled"].includes(status)) return "cancelled";
  if (["created", "pending"].includes(status)) return "pending";
  return "unknown";
}
