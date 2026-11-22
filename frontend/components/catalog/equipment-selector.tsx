"use client";

import { useState } from "react";
import Link from "next/link";
import { FiCheckCircle, FiCpu, FiCompass, FiArrowLeft, FiFileText } from "react-icons/fi";
import type { NavCategory } from "../../lib/nav-category";
import { getCategoryUrl } from "../../lib/category-url";

export type SelectorIndustry = {
  id: number;
  slug: string;
  name_fa: string;
  name_en: string;
  description_fa: string;
  description_en: string;
  image?: string | null;
};

interface EquipmentSelectorProps {
  locale?: string;
  industries: SelectorIndustry[];
  categories: NavCategory[];
}

export function EquipmentSelector({ locale = "fa", industries = [], categories = [] }: EquipmentSelectorProps) {
  const english = locale === "en";
  // Filter out demo-labeled items if any
  const liveIndustries = industries.filter((ind) => !ind.name_fa.startsWith("[DEMO]"));
  const activeIndustries = liveIndustries.length > 0 ? liveIndustries : industries;

  const [selectedIndustryId, setSelectedIndustryId] = useState<number>(() => activeIndustries[0]?.id || 0);

  if (!activeIndustries.length && !categories.length) {
    return null;
  }

  const currentIndustry = activeIndustries.find((item) => item.id === selectedIndustryId) || activeIndustries[0];

  // Key HVAC equipment lines from server categories
  const hvacEquipmentCategories = categories.slice(0, 8);

  const getIndustryName = (item: SelectorIndustry) => (english && item.name_en ? item.name_en : item.name_fa);
  const getIndustryDesc = (item: SelectorIndustry) => (english && item.description_en ? item.description_en : item.description_fa);

  return (
    <section className="enterprise-section site-container equipment-selector-wrap" aria-labelledby="selector-heading">
      <div className="equipment-selector-card">
        <header className="equipment-selector-header">
          <div className="selector-badge">
            <FiCompass aria-hidden="true" />
            <span>{english ? "System Selection Guide" : "راهنمای مهندسی انتخاب و کاربری کالا"}</span>
          </div>
          <h2 id="selector-heading" className="selector-title">
            {english ? "Select Equipment Tailored to Your Application" : "انتخاب هوشمند سیستم متناسب با کاربری پروژه"}
          </h2>
          <p className="selector-subtitle">
            {english
              ? "Choose your facility type to review tailored HVAC engineering solutions and view compatible equipment."
              : "نوع کاربری پروژه خود را از فهرست زیر انتخاب کنید تا مشخصات و تجهیزات تخصصی متناسب با آن نمایش داده شود."}
          </p>
        </header>

        <div className="equipment-selector-body">
          {/* Industry Tabs (Loaded from server) */}
          {activeIndustries.length > 0 && (
            <div className="selector-industry-strip" role="tablist" aria-label="انتخاب نوع کاربری">
              {activeIndustries.map((ind) => {
                const isSelected = ind.id === currentIndustry?.id;
                return (
                  <button
                    key={ind.id}
                    type="button"
                    role="tab"
                    aria-selected={isSelected}
                    className={`selector-industry-tab ${isSelected ? "is-active" : ""}`}
                    onClick={() => setSelectedIndustryId(ind.id)}
                  >
                    <span>{getIndustryName(ind)}</span>
                  </button>
                );
              })}
            </div>
          )}

          {/* Selected Industry Detail Box */}
          {currentIndustry && (
            <div className="selector-detail-box">
              <div className="selector-detail-header">
                <div className="selector-detail-tag">
                  <FiCpu aria-hidden="true" />
                  <span>{english ? "Application Requirements & Systems" : "الزامات فنی و سیستم‌های پیشنهادی"}</span>
                </div>
                <h3 className="selector-detail-title">{getIndustryName(currentIndustry)}</h3>
                {getIndustryDesc(currentIndustry) ? (
                  <p className="selector-detail-desc">{getIndustryDesc(currentIndustry)}</p>
                ) : (
                  <p className="selector-detail-desc">
                    {english
                      ? "Custom-engineered chilling and air-handling packages designed for continuous operation and strict thermal efficiency."
                      : "سیستم‌های سرمایش، تهویه مطبوع و پایانه طراحی‌شده متناسب با اقلیم و الزامات بار برودتی این کاربری."}
                  </p>
                )}
              </div>

              {/* Server-loaded equipment categories */}
              {hvacEquipmentCategories.length > 0 && (
                <div className="selector-categories-group">
                  <h4 className="selector-categories-title">
                    {english ? "Compatible Equipment Lines:" : "تجهیزات و خطوط تولید مرتبط:"}
                  </h4>
                  <div className="selector-categories-pills">
                    {hvacEquipmentCategories.map((cat) => (
                      <Link
                        key={cat.id}
                        href={getCategoryUrl(cat, locale)}
                        className="selector-category-pill"
                        title={cat.name_fa}
                      >
                        <FiCheckCircle className="pill-check" aria-hidden="true" />
                        <span>{cat.name_fa}</span>
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="selector-actions-row">
                <Link
                  href={`/${locale}/shop?q=${encodeURIComponent(currentIndustry.name_fa)}`}
                  className="selector-btn-primary"
                >
                  <span>{english ? "Browse Matching Equipment" : "مشاهده تجهیزات مرتبط در کاتالوگ"}</span>
                  <FiArrowLeft aria-hidden="true" />
                </Link>
                <Link
                  href={`/${locale}/rfq?category=${encodeURIComponent(currentIndustry.name_fa)}`}
                  className="selector-btn-secondary"
                >
                  <FiFileText aria-hidden="true" />
                  <span>{english ? "Request Engineering Quotation" : "استعلام قیمت و پیش‌فاکتور مهندسی"}</span>
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}