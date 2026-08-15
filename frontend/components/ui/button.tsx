import Link from "next/link";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "./utils";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  href?: string;
  children: ReactNode;
};

export function Button({ variant = "primary", size = "md", loading = false, href, className, children, disabled, type, ...props }: ButtonProps) {
  const classes = cn("ui-button", `ui-button--${variant}`, `ui-button--${size}`, className);
  const content = <>{loading && <span className="ui-button__spinner" aria-hidden="true" />}{children}</>;
  if (href) return <Link href={href} className={classes} aria-busy={loading || undefined}>{content}</Link>;
  return <button type={type ?? "button"} className={classes} disabled={disabled || loading} aria-busy={loading || undefined} {...props}>{content}</button>;
}
