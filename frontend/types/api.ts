export interface PaginatedResponse<T> { count: number; next: string | null; previous: string | null; results: T[]; }

export type CompanyInfo = {
  id: number;
  name_fa: string;
  logo: string | null;
  description: string;
  address: string;
  phone: string;
  mobile: string;
  email: string;
  website: string;
  working_hours: string;
};

export type SiteHeroBanner = { id: number; desktop_image: string; mobile_image: string; title: string; description: string; button: { text: string; link: string } | null };
export type SiteHero = { title: string; slogan: string; description: string; hero_image: string | null; mobile_hero_image: string | null; buttons: { text: string; link: string; variant: "primary" | "secondary" }[]; banners?: SiteHeroBanner[] };

export type EditorialCategory = { id: number; slug: string; name_fa: string; name_en: string; description_fa?: string; description_en?: string; display_order?: number };
export type EditorialContextProduct = { id: number; code: string; name: string; slug: string };
export type EditorialContextCategory = { id: number; code: string; name_fa: string; name_en: string; slug: string };
export type EditorialContextBrand = { id: number; name: string; slug: string | null };
export type EditorialContextIndustry = { id: number; slug: string; name_fa: string; name_en: string };
export type EditorialContextCapability = { id: number; slug: string; title_fa: string; title_en: string };
export type EditorialArticle = {
  id: number;
  slug: string;
  content_type: "news" | "event" | "technical_article" | "product_guide" | "buying_guide" | "product_announcement" | string;
  content_type_label?: string;
  title: string;
  title_fa: string;
  title_en: string;
  excerpt: string;
  excerpt_fa: string;
  excerpt_en: string;
  body?: string;
  body_fa?: string;
  body_en?: string;
  featured_image: string | null;
  published_at: string | null;
  is_featured: boolean;
  category: EditorialCategory | null;
  related_products: EditorialContextProduct[];
  related_catalog_categories: EditorialContextCategory[];
  related_brands: EditorialContextBrand[];
  related_industries: EditorialContextIndustry[];
  related_capabilities: EditorialContextCapability[];
  seo_title?: string;
  seo_title_fa?: string;
  seo_title_en?: string;
  seo_description?: string;
  seo_description_fa?: string;
  seo_description_en?: string;
};

export type FAQEntry = {
  id: number;
  slug: string;
  faq_type: "general" | "product" | "technical" | "warranty" | "ordering" | "support" | "installation" | "maintenance" | string;
  faq_type_label?: string;
  question: string;
  question_fa: string;
  question_en: string;
  answer: string;
  answer_fa: string;
  answer_en: string;
  display_order: number;
  related_products: EditorialContextProduct[];
  related_categories: EditorialContextCategory[];
  related_industries: EditorialContextIndustry[];
  related_capabilities: EditorialContextCapability[];
  related_articles: { id: number; slug: string; title_fa: string; title_en: string; content_type: string }[];
};
