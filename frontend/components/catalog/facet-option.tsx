import type { FacetOption as FacetOptionData } from "./facet-types";

export function FacetOption({ option, type = "checkbox", onChange }: { option: FacetOptionData; type?: "checkbox" | "single_select" | "boolean" | "category"; onChange: (selected: boolean) => void }) {
  const isDemo = /^\[DEMO\]/i.test(option.label), label = option.label.replace(/^\[DEMO\]\s*/i, "");
  return <label className="facet-option"><input type={type === "single_select" ? "radio" : "checkbox"} checked={Boolean(option.selected)} onChange={(event) => onChange(event.target.checked)} /><span>{label}{isDemo && <small className="facet-demo-badge">نمونه</small>}</span>{option.count !== undefined && <small className="facet-option-count">{option.count.toLocaleString("fa-IR")}</small>}</label>;
}
