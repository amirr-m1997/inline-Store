import type { ReactNode } from "react";
import { cn } from "./utils";

export function Toast({ children, variant = "success" }: { children: ReactNode; variant?: "success" | "error" | "info" }) {
  return <div className={cn("ui-toast", `ui-toast--${variant}`)} role={variant === "error" ? "alert" : "status"}>{children}</div>;
}
