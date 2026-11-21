"use client";

import { useState } from "react";
import Link from "next/link";
import { FiCheckCircle, FiCpu, FiCompass, FiArrowLeft, FiSliders, FiFileText } from "react-icons/fi";

interface EquipmentSelectorProps {
  locale?: string;
}

type ApplicationType = "industrial" | "commercial" | "office" | "hospital" | "residential";
type CapacityType = "under-30" | "30-100" | "100-250" | "over-250";

interface Recommendation {
  title: string;
  subtitle: string;
  highlights: string[];
  suggestedSeries: string;
  catalogCategory: string;
  catalogFilterUrl: string;
}

export function EquipmentSelector({ locale = "fa" }: EquipmentSelectorProps) {
  const english = locale === "en";
  const [application, setApplication] = useState<ApplicationType>("industrial");
  const [capacity, setCapacity] = useState<CapacityType>("100-250");

  const applications = [
    { id: "industrial", label: english ? "Industrial / Factories" : "صنعتی و خطوط تولید", icon: "🏭" },
    { id: "commercial", label: english ? "Commercial / Malls" : "تجاری و مال‌ها", icon: "🏬" },
    { id: "hospital", label: english ? "Hospitals / Cleanrooms" : "بیمارستانی و کلین‌روم", icon: "🏥" },
    { id: "office", label: english ? "Offices / Towers" : "اداری و برج‌ها", icon: "🏢" },
    { id: "residential", label: english ? "Luxury Residential" : "مسکونی و ویلایی", icon: "🏡" },
  ] as const;

  const capacities = [
    { id: "under-30", label: english ? "< 30 TR (Compact)" : "کمتر از ۳۰ تن (سبک)" },
    { id: "30-100", label: english ? "30 - 100 TR (Medium)" : "۳۰ تا ۱۰۰ تن (متوسط)" },
    { id: "100-250", label: english ? "100 - 250 TR (Heavy)" : "۱۰۰ تا ۲۵۰ تن (سنگین)" },
    { id: "over-250", label: english ? "> 250 TR (Megawatt)" : "بیش از ۲۵۰ تن (پروژه‌ای)" },
  ] as const;

  const getRecommendation = (): Recommendation => {
    if (application === "hospital") {
      return {
        title: english ? "Hygienic Air Handling Unit & Dual Water-Cooled Chiller" : "هواساز هایژنیک استاندارد DIN 1946 و چیلر آب‌خنک با ریداندنسی",
        subtitle: english ? "Designed for 100% fresh air, HEPA/ULPA filtration, and strict humidity/temperature control." : "مجهز به فیلتراسیون هپا/اولپا، سیستم هوادهی تمام‌تازه و کنترل دقیق دما و رطوبت اتاق‌های عمل و فضاهای تمیز.",
        highlights: [
          english ? "Full compliance with Eurovent & DIN 1946-4 standards" : "انطباق کامل با استانداردهای Eurovent و DIN 1946-4",
          english ? "Dual independent refrigerant circuits for 100% redundancy" : "دو مدار تبرید کاملاً مستقل جهت تداوم کارکرد بدون وقفه (Redundancy)",
          english ? "Stainless steel drain pans and antimicrobial casing" : "کف استنلس استیل با شیب دوطرفه و عایق ضدمیکروب و ضدباکتری",
        ],
        suggestedSeries: "HAHU-Series & MWC Series",
        catalogCategory: english ? "Hygienic AHU & Water-Cooled Chiller" : "هواساز بیمارستانی و چیلر صنعتی",
        catalogFilterUrl: `/${locale}/shop?q=چیلر`,
      };
    }

    if (capacity === "under-30") {
      return {
        title: english ? "Rooftop Packaged Unit / Scroll Air-Cooled Chiller" : "پکیج یونیت یکپارچه پشت‌بامی و مینی‌چیلر اسکرال",
        subtitle: english ? "Cost-effective, compact footprint with plug-and-play installation for targeted cooling." : "بهترین گزینه برای پروژه‌های مستقل، نصب آسان بدون نیاز به موتورخانه مرکزی و راندمان فصلی فوق‌العاده.",
        highlights: [
          english ? "Compact footprint with low operating noise level" : "اشغال حداقل فضای مفید بام و صدای کارکرد فوق‌العاده پایین",
          english ? "High-efficiency Copeland/Danfoss Scroll compressors" : "مجهز به کمپرسورهای اسکرال کم‌مصرف کوپلند یا دانفوس",
          english ? "Independent micro-channel or copper-aluminum coils" : "کویل‌های فین پلیت آلومینیومی با پوشش ضدخوردگی گلدفین",
        ],
        suggestedSeries: "RPU & Mini-Scroll Series",
        catalogCategory: english ? "Rooftop Packages" : "پکیج یونیت و مینی‌چیلر",
        catalogFilterUrl: `/${locale}/shop?q=پکیج`,
      };
    }

    if (capacity === "over-250") {
      return {
        title: english ? "Industrial Water-Cooled Screw / Centrifugal Chiller Plant" : "چیلر سانتریفیوژ و اسکرو آب‌خنک مگاواتی با بالاترین ضریب عملکرد (COP)",
        subtitle: english ? "Engineered for 24/7 continuous industrial loads, refinery complexes, and landmark towers." : "طراحی شده برای بار مداوم ۲۴/۷، کارخانجات فولاد، پتروشیمی، داروسازی و مجتمع‌های عظیم با حداقل مصرف انرژی برق.",
        highlights: [
          english ? "Ultra-high COP (> 5.8) with VFD Variable Frequency Drive" : "ضریب راندمان بالا (COP > 5.8) با کنترل دور اینورتر (VFD)",
          english ? "Shell & Tube evaporator with high-efficiency inner-grooved tubes" : "اواپراتور و کندانسور پوسته-لوله استاندارد ASME با لوله‌های فین‌دار مسی",
          english ? "Industrial PLC controller with BMS Modbus/BacNet integration" : "سیستم کنترل پیشرفته صنعتی مجهز به پورت شبکه هوشمند ساختمان (BMS)",
        ],
        suggestedSeries: "MWC-Heavy & Centrifugal Series",
        catalogCategory: english ? "Centrifugal & Heavy Screw Chiller" : "چیلر سانتریفیوژ و اسکرو سنگین",
        catalogFilterUrl: `/${locale}/shop?q=چیلر`,
      };
    }

    // Default: 30-100 or 100-250 TR for Industrial/Commercial/Office
    return {
      title: english ? "Air-Cooled Screw Chiller with Inverter / Economizer" : "چیلر تراکمی اسکرو هواخنک با کمپرسور نیمه‌بسته صنعتی",
      subtitle: english ? "Zero water consumption, robust operation in harsh ambient conditions up to 52°C." : "بدون نیاز به آب و برج خنک‌کننده، راندمان بالا حتی در دمای محیطی بالای ۵۲ درجه سانتی‌گراد مناطق گرمسیری.",
      highlights: [
        english ? "Semi-hermetic twin-screw compressors with 4-step or stepless capacity control" : "کمپرسور دو اسکرو نیمه‌بسته با کنترل ظرفیت پله‌ای یا خطی بدون شوک الکتریکی",
        english ? "Ecological refrigerant R134a / R410A with zero ODP" : "سازگار با محیط زیست با مبرد R134a با تخریب صفر لایه اوزون",
        english ? "Axial condenser fans with aerodynamic low-noise profile" : "فن‌های آکسیال کم‌صدا مجهز به محافظ‌های صنعتی ضدپاشش و ضدگردوغبار",
      ],
      suggestedSeries: "MAC-Screw Series",
      catalogCategory: english ? "Air-Cooled Screw Chillers" : "چیلر اسکرو هواخنک",
      catalogFilterUrl: `/${locale}/shop?q=چیلر`,
    };
  };

  const rec = getRecommendation();

  return (
    <section className="equipment-selector-section" aria-labelledby="selector-heading">
      <div className="equipment-selector-container">
        <header className="equipment-selector-header">
          <div className="selector-badge">
            <FiCompass aria-hidden="true" />
            <span>{english ? "System Sizing & Selection Guide" : "راهنمای مهندسی انتخاب و محاسبه سریع"}</span>
          </div>
          <h2 id="selector-heading" className="selector-title">
            {english ? "Find the Right HVAC Equipment for Your Project" : "انتخاب هوشمند سیستم تهویه مطبوع و برودت صنعتی"}
          </h2>
          <p className="selector-subtitle">
            {english
              ? "Select your building usage and required cooling capacity to discover the tailored engineering solution."
              : "نوع کاربری پروژه و تناژ تقریبی مورد نیاز خود را مشخص کنید تا سیستم مهندسی بهینه فوراً به شما پیشنهاد شود."}
          </p>
        </header>

        <div className="equipment-selector-grid">
          {/* Controls Column */}
          <div className="selector-controls-card">
            {/* Step 1: Application */}
            <div className="selector-group">
              <label className="selector-group-label">
                <span className="step-num">۱</span>
                <span>{english ? "Building & Application Type" : "نوع کاربری و محیط نصب"}</span>
              </label>
              <div className="selector-chips" role="radiogroup" aria-label="نوع کاربری">
                {applications.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    role="radio"
                    aria-checked={application === item.id}
                    className={`selector-chip ${application === item.id ? "is-selected" : ""}`}
                    onClick={() => setApplication(item.id)}
                  >
                    <span className="chip-icon">{item.icon}</span>
                    <span className="chip-text">{item.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Step 2: Capacity */}
            <div className="selector-group">
              <label className="selector-group-label">
                <span className="step-num">۲</span>
                <span>{english ? "Estimated Cooling Capacity" : "تناژ برودتی تقریبی مورد نیاز (TR)"}</span>
              </label>
              <div className="selector-capacity-options" role="radiogroup" aria-label="تناژ برودتی">
                {capacities.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    role="radio"
                    aria-checked={capacity === item.id}
                    className={`selector-capacity-btn ${capacity === item.id ? "is-selected" : ""}`}
                    onClick={() => setCapacity(item.id)}
                  >
                    <FiSliders aria-hidden="true" className="capacity-icon" />
                    <span>{item.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Recommendation Column */}
          <div className="selector-recommendation-card">
            <div className="recommendation-header">
              <div className="rec-eyebrow">
                <FiCpu aria-hidden="true" />
                <span>{english ? "Recommended System" : "سیستم پیشنهادی مهندسی"}</span>
              </div>
              <h3 className="rec-title">{rec.title}</h3>
              <p className="rec-desc">{rec.subtitle}</p>
            </div>

            <div className="recommendation-features">
              <h4 className="features-title">
                {english ? "Key Engineering Specs:" : "ویژگی‌های کلیدی و مزایای فنی:"}
              </h4>
              <ul className="features-list">
                {rec.highlights.map((point, idx) => (
                  <li key={idx}>
                    <FiCheckCircle className="feat-check-icon" aria-hidden="true" />
                    <span>{point}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="recommendation-actions">
              <Link href={rec.catalogFilterUrl} className="rec-cta-primary">
                <span>{english ? "Browse Matching Catalog" : "مشاهده مدل‌های مرتبط در کاتالوگ"}</span>
                <FiArrowLeft className="cta-arrow" aria-hidden="true" />
              </Link>
              <Link
                href={`/${locale}/rfq?category=${encodeURIComponent(rec.catalogCategory)}`}
                className="rec-cta-secondary"
              >
                <FiFileText aria-hidden="true" />
                <span>{english ? "Request Engineering Quote" : "درخواست استعلام فنی و پیش‌فاکتور"}</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}