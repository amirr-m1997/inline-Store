import type { ProductDetail, ProductDocument, ProductSummary } from "./types";

type ProductDetailInput = {
  id: number; name_fa: string; slug: string; sku: string; unit: string; name_en?: string; description?: string;
  inventory?: { allowed_for_cart?: number | null } | null;
  category_tree?: { id: number; name_fa: string; slug: string }[] | null;
  images?: { url: string; alt_text?: string | null; alt_fa?: string | null; is_primary?: boolean }[] | null;
  pricing?: { final_price?: string | null; price?: string | null; discount_percentage?: string | null } | null;
  technical_specifications?: ProductDetail["specifications"] | null;
  service_advantages?: { id: number; title_fa: string; description_fa?: string; icon?: string }[] | null;
  related_products?: { id: number; name_fa: string; slug: string; code: string; unit: string; primary_image?: string | null }[] | null;
  documents?: { id: number | string; title: string; type: string; file_url: string; file_name?: string | null; display_name?: string | null; size?: number | string | null; revision?: string | null; language?: string | null }[] | null;
};

export function toProductSummary(raw: { id:number; name:string; slug:string; code:string; unit:string; available_quantity:number|null; category:{name_fa:string}|null; images:{image:string;alt_text:string;alt_fa?:string;is_primary?:boolean}[] | null | undefined; price:{original_amount:string;final_amount:string;discount_percentage:string}|null }): ProductSummary {
  const images = Array.isArray(raw.images) ? raw.images : [];
  return { id:raw.id, name:raw.name, slug:raw.slug, code:raw.code, unit:raw.unit, category:raw.category ? { name:raw.category.name_fa } : undefined, media:images.map((image) => ({ url:image.image, alt:image.alt_fa || image.alt_text, isPrimary:image.is_primary })), pricing:raw.price ? { originalAmount:raw.price.original_amount, finalAmount:raw.price.final_amount, discountPercentage:raw.price.discount_percentage, currency:"IRR" } : undefined, availability:{ quantity:raw.available_quantity, availableToCart:raw.available_quantity ?? 0 } };
}

const KNOWN_DOCUMENT_TYPES = new Set(["datasheet", "manual", "cad", "certificate", "catalogue", "other"]);

export function toProductDetail(raw: ProductDetailInput): ProductDetail { const images = Array.isArray(raw.images) ? raw.images : []; const categoryTree = Array.isArray(raw.category_tree) ? raw.category_tree : []; const advantages = Array.isArray(raw.service_advantages) ? raw.service_advantages : []; const related = Array.isArray(raw.related_products) ? raw.related_products : []; const documents = raw.documents || []; const summary = toProductSummary({ id:raw.id, name:raw.name_fa, slug:raw.slug, code:raw.sku, unit:raw.unit, available_quantity:raw.inventory?.allowed_for_cart ?? null, category:null, images:images.map((image) => ({ image:image.url, alt_text:image.alt_text ?? "", alt_fa:image.alt_fa ?? undefined, is_primary:image.is_primary })), price:raw.pricing?.final_price ? { original_amount:raw.pricing.price ?? raw.pricing.final_price, final_amount:raw.pricing.final_price, discount_percentage:raw.pricing.discount_percentage || "0" } : null }); const docs: ProductDocument[] = documents.map((document) => ({ id:String(document.id), title:document.title, type:(KNOWN_DOCUMENT_TYPES.has(document.type) ? document.type : "other") as ProductDocument["type"], fileUrl:document.file_url, fileName:document.file_name || document.display_name || document.title, size:typeof document.size === "number" ? document.size : Number(document.size) || undefined, revision:document.revision || undefined, language:document.language || undefined })); return { ...summary, sku:raw.sku, nameEn:raw.name_en, description:raw.description, categories:categoryTree.map((category) => ({ id:category.id, name:category.name_fa, slug:category.slug })), specifications:raw.technical_specifications ?? [], serviceAdvantages:advantages.map((item) => ({ id:item.id, title:item.title_fa, description:item.description_fa, icon:item.icon })), variants:[], relationships:related.map((item) => ({ type:"related", product:{ id:item.id, name:item.name_fa, slug:item.slug, code:item.code, unit:item.unit, media:item.primary_image ? [{url:item.primary_image,alt:item.name_fa}] : [], availability:{quantity:null,availableToCart:0} } })), documents:docs }; }
