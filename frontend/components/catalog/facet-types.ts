export type FacetType = "checkbox" | "single_select" | "range" | "boolean" | "category";
export type FacetOption = { value: string; label: string; count?: number; selected?: boolean };
export type CatalogFacet = { name: string; label?: string; type: FacetType; options?: FacetOption[]; counts?: Record<string, number>; min?: number; max?: number; unit?: string; selected?: unknown };
