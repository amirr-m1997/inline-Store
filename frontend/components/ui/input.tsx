import type { InputHTMLAttributes } from "react";
import { cn } from "./utils";

type InputProps = InputHTMLAttributes<HTMLInputElement> & { error?: boolean };

export function Input({ className, error = false, ...props }: InputProps) {
  return <input className={cn("ui-input", error && "ui-input--error", className)} aria-invalid={error || undefined} {...props} />;
}
