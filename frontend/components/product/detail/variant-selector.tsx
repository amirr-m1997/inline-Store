"use client";

import { useMemo, useState } from "react";
import type { ProductDetail, ProductVariant, VariantSelection } from "../../../lib/product/types";

export function VariantSelector({ product, onChange }: { product: ProductDetail; onChange?: (selection: VariantSelection) => void }) {
  const [selected, setSelected] = useState<Record<string, string>>({});
  const groups = useMemo(() => { const values = new Map<string, string[]>(); product.variants.forEach((variant) => variant.attributes.forEach((attribute) => { const group = values.get(attribute.name) || []; if (!group.includes(attribute.value)) group.push(attribute.value); values.set(attribute.name, group); })); return Array.from(values.entries()); }, [product.variants]);
  if (!product.variants.length) return <div className="variant-selector variant-selector-empty" aria-live="polite" />;
  const resolve = (next: Record<string, string>) => product.variants.find((variant) => variant.attributes.every((attribute) => next[attribute.name] === attribute.value));
  const update = (name: string, value: string) => { const next = { ...selected, [name]: value }; setSelected(next); onChange?.({ selected: next, resolvedVariant: resolve(next) }); };
  const isAvailable = (name: string, value: string) => product.variants.some((variant) => variant.attributes.some((attribute) => attribute.name === name && attribute.value === value) && variant.attributes.every((attribute) => attribute.name === name || !selected[attribute.name] || selected[attribute.name] === attribute.value));
  return <section className="variant-selector" aria-label="انتخاب مشخصات محصول">{groups.map(([name, values]) => <fieldset key={name}><legend>{name}</legend><div>{values.map((value) => { const disabled = !isAvailable(name, value); return <button key={value} type="button" className={selected[name] === value ? "selected" : ""} aria-label={`${value}${disabled ? "، با انتخاب فعلی در دسترس نیست" : ""}`} aria-pressed={selected[name] === value} disabled={disabled} onClick={() => update(name, value)}>{value}</button>; })}</div></fieldset>)}</section>;
}
