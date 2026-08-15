import type { CatalogFacet } from "./facet-types";
import { FacetGroup } from "./facet-group";

export function FacetSidebar({ facets, onOptionChange, onRangeChange }: { facets: CatalogFacet[]; onOptionChange: (facet: CatalogFacet, value: string, selected: boolean) => void; onRangeChange: (facet: CatalogFacet, value: { min?: string; max?: string }) => void }) {
  if (!facets.length) return null;
  return <aside className="facet-sidebar" aria-label="فیلترهای کاتالوگ">{facets.map((facet) => <FacetGroup key={facet.name} facet={facet} onOptionChange={(value, selected) => onOptionChange(facet, value, selected)} onRangeChange={(value) => onRangeChange(facet, value)} />)}</aside>;
}
