import { useEffect, useRef, useState } from "react";

export function RangeFilter({ facet, onChange }: { facet: { name: string; min?: number; max?: number; unit?: string; selected?: unknown }; onChange?: (value: { min?: string; max?: string }) => void }) {
  const selected = facet.selected && typeof facet.selected === "object" ? facet.selected as { min?: string; max?: string } : {};
  const [minimum, setMinimum] = useState(selected.min || ""), [maximum, setMaximum] = useState(selected.max || "");
  const initialRender = useRef(true);
  const onChangeRef = useRef(onChange);
  useEffect(() => { onChangeRef.current = onChange; }, [onChange]);
  useEffect(() => {
    if (initialRender.current) {
      initialRender.current = false;
      return;
    }
    if (!onChangeRef.current) return;
    const timer = window.setTimeout(() => onChangeRef.current?.({ min: minimum || undefined, max: maximum || undefined }), 450);
    return () => window.clearTimeout(timer);
  }, [maximum, minimum]);
  return <div className="facet-range"><label><span>از</span><div className="facet-range-input"><input aria-label={`${facet.name} از`} value={minimum} inputMode="decimal" placeholder={facet.min?.toString()} onChange={(event) => setMinimum(event.target.value)} />{facet.unit && <small aria-hidden="true">{facet.unit}</small>}</div></label><label><span>تا</span><div className="facet-range-input"><input aria-label={`${facet.name} تا`} value={maximum} inputMode="decimal" placeholder={facet.max?.toString()} onChange={(event) => setMaximum(event.target.value)} />{facet.unit && <small aria-hidden="true">{facet.unit}</small>}</div></label></div>;
}
