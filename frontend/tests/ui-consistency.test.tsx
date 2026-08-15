import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { EmptyState } from "../components/ui/empty-state";
import { ErrorState } from "../components/ui/error-state";
import { FormField } from "../components/ui/form-field";

describe("shared UI consistency primitives", () => {
  it("communicates loading and disabled button state", () => {
    render(<Button loading>ذخیره</Button>);
    const button = screen.getByRole("button", { name: "ذخیره" });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
  });

  it("exposes form errors as alerts and preserves status text", () => {
    render(<FormField label="ایمیل" error="ایمیل معتبر نیست."><input aria-label="ایمیل" /></FormField>);
    expect(screen.getByRole("alert")).toHaveTextContent("ایمیل معتبر نیست.");
  });

  it("keeps empty, error, and status badges semantic", () => {
    render(<><Badge variant="success">موجود</Badge><EmptyState title="بدون نتیجه" /><ErrorState title="خطا" /></>);
    expect(screen.getByText("موجود")).toHaveClass("ui-badge--success");
    expect(screen.getByText("بدون نتیجه")).toBeInTheDocument();
    expect(screen.getAllByRole("alert").at(-1)).toHaveTextContent("خطا");
  });
});
