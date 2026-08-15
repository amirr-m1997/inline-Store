"use client";

import { useEffect, useState } from "react";
import type { CompanyInfo } from "../types/api";
import { getCompany } from "../lib/api/content";

export function useCompanyInfo(initialCompany: CompanyInfo | null = null) {
  const [company, setCompany] = useState<CompanyInfo | null>(initialCompany);
  useEffect(() => {
    if (initialCompany) return;
    getCompany<CompanyInfo>()
      .then((data: CompanyInfo | null) => setCompany(data))
      .catch(() => setCompany(null));
  }, [initialCompany]);
  return company;
}
