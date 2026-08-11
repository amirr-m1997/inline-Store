"use client";

import { useEffect, useState } from "react";
import type { CompanyInfo } from "../types/api";

export function useCompanyInfo() {
  const [company, setCompany] = useState<CompanyInfo | null>(null);
  useEffect(() => {
    fetch("/api/v1/company/", { cache: "no-store" })
      .then((response) => (response.ok ? response.json() : null))
      .then((data: CompanyInfo | null) => setCompany(data))
      .catch(() => setCompany(null));
  }, []);
  return company;
}
