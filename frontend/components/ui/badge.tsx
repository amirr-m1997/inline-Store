import type { HTMLAttributes } from "react";
import { cn } from "./utils";

export function Badge({ className, ...props }: HTMLAttributes<HTMLSpanElement> & { variant?: "default" | "success" | "danger" | "warning" }) {
  const { variant = "default", ...rest } = props;
  return <span className={cn("ui-badge", `ui-badge--${variant}`, className)} {...rest} />;
}
