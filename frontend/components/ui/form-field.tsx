import type { ReactNode } from "react";

export function FormField({ label, htmlFor, required, error, children }: { label: string; htmlFor?: string; required?: boolean; error?: string; children: ReactNode }) {
  return <label className="ui-form-field" htmlFor={htmlFor}><span>{label}{required && " *"}</span>{children}{error && <small role="alert">{error}</small>}</label>;
}
