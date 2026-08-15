"use client";

import { useState } from "react";
import type { CatalogFacet } from "./facet-types";
import { FacetOption } from "./facet-option";
import { RangeFilter } from "./range-filter";

export function FacetGroup({ facet, onOptionChange, onRangeChange }: { facet: CatalogFacet; onOptionChange: (value: string, selected: boolean) => void; onRangeChange?: (value: { min?: string; max?: string }) => void }) {
  const optionType = facet.type === "single_select" ? "single_select" : facet.type === "boolean" ? "boolean" : facet.type === "category" ? "category" : "checkbox";
  const displayLabel = (facet.label || facet.name).replace(/^\[DEMO\]\s*/i, "");
  const options = facet.options || [], [expanded, setExpanded] = useState(false), visibleOptions = expanded ? options : options.slice(0, 8), hasMore = options.length > 8;
  return <section className="facet-group"><h2>{displayLabel}{(facet.label || facet.name).match(/^\[DEMO\]/i) && <small className="facet-demo-badge">نمونه</small>}</h2>{facet.type === "range" ? <RangeFilter facet={{ ...facet, name: displayLabel }} onChange={onRangeChange} /> : <><div>{visibleOptions.map((option) => <FacetOption key={option.value} option={option} type={optionType} onChange={(selected) => onOptionChange(option.value, selected)} />)}</div>{hasMore && <button type="button" className="facet-expand-button" onClick={() => setExpanded((value) => !value)}>{expanded ? "نمایش کمتر" : `نمایش ${Math.min(options.length - 8, options.length).toLocaleString("fa-IR")} گزینهٔ دیگر`}</button>}</>}</section>;
}
