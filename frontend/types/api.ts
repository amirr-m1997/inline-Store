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

export type SiteHero = { title: string; slogan: string; description: string; hero_image: string | null; mobile_hero_image: string | null; buttons: { text: string; link: string; variant: "primary" | "secondary" }[] };
