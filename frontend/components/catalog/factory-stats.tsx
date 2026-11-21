import { FiAward, FiShield, FiTrendingUp, FiMapPin, FiCheckCircle } from "react-icons/fi";

interface FactoryStatsProps {
  locale?: string;
}

export function FactoryStats({ locale = "fa" }: FactoryStatsProps) {
  const english = locale === "en";

  const stats = [
    {
      value: "۴۰+",
      valueEn: "40+",
      label: english ? "Years of Engineering Heritage" : "سال سابقه درخشان در صنعت برودت و تهویه",
      description: english ? "Continuous innovation and manufacturing since 1985" : "تولید مستمر تجهیزات سنگین سرمایشی از سال ۱۳۶۹",
      icon: FiAward,
    },
    {
      value: "۱۲۰۰+",
      valueEn: "1,200+",
      label: english ? "Major National & Industrial Projects" : "پروژه بزرگ ملی و بیمارستانی اجرا شده",
      description: english ? "Installed across oil & gas, medical, and commercial infrastructure" : "نیروگاه‌ها، پتروشیمی‌ها، بیمارستان‌های تخصصی و برج‌های ملی",
      icon: FiTrendingUp,
    },
    {
      value: "۴۵,۰۰۰+",
      valueEn: "45,000+",
      label: english ? "m² Industrial Manufacturing Facility" : "مترمربع مساحت کارخانجات تولیدی و آزمایشگاهی",
      description: english ? "Modern production lines with full climatic testing chambers" : "خطوط تمام مکانیزه و آزمایشگاه‌های پیشرفته تست عملکرد چیلر",
      icon: FiShield,
    },
    {
      value: "۳۶+",
      valueEn: "36+",
      label: english ? "Authorized After-Sales Centers" : "مرکز خدمات پس از فروش و نمایندگی تخصصی",
      description: english ? "Nationwide coverage with rapid on-site maintenance" : "پوشش سراسری در کلیه استان‌ها با اعزام سریع تکنسین‌های مجرب",
      icon: FiMapPin,
    },
  ];

  const certifications = [
    english ? "ISO 9001:2015 Quality Management" : "گواهینامه مدیریت کیفیت ISO 9001:2015",
    english ? "CE European Conformity Mark" : "نشان انطباق استاندارد اروپا CE",
    english ? "National Standard of Iran (ISIRI)" : "پروانه نشان استاندارد ملی ایران",
    english ? "Eurovent Energy Rating Compliant" : "انطباق طراحی با استانداردهای راندمان Eurovent",
  ];

  return (
    <section className="factory-stats-section" aria-labelledby="stats-heading">
      <div className="factory-stats-bg-grid" aria-hidden="true" />
      <div className="factory-stats-container">
        <header className="factory-stats-header">
          <span className="stats-tag">
            {english ? "Factory Milestones & Trust" : "افتخارات، توانمندی و سابقه صنعتی"}
          </span>
          <h2 id="stats-heading" className="stats-title">
            {english ? "Powering National Infrastructure for Decades" : "پیشرو در طراحی و تولید تأسیسات حیاتی و پروژه‌های ملی"}
          </h2>
          <p className="stats-subtitle">
            {english
              ? "With dedicated production infrastructure, rigorous testing, and nation-wide support, we engineer reliability."
              : "تکیه بر مهندسی دقیق، استفاده از قطعات تراز اول جهانی، و پشتیبانی فنی ۲۴ ساعته در سخت‌ترین شرایط اقلیمی ایران."}
          </p>
        </header>

        <div className="factory-stats-grid">
          {stats.map((stat, idx) => {
            const Icon = stat.icon;
            return (
              <div key={idx} className="stat-card">
                <div className="stat-card-icon-wrap">
                  <Icon className="stat-icon" aria-hidden="true" />
                </div>
                <div className="stat-card-body">
                  <span className="stat-number">
                    <bdi>{english ? stat.valueEn : stat.value}</bdi>
                  </span>
                  <h3 className="stat-label">{stat.label}</h3>
                  <p className="stat-desc">{stat.description}</p>
                </div>
              </div>
            );
          })}
        </div>

        <div className="factory-certifications-bar">
          <span className="certs-label">
            {english ? "Certified Quality & Standards:" : "گواهینامه‌ها و استانداردهای بین‌المللی:"}
          </span>
          <div className="certs-chips">
            {certifications.map((cert, idx) => (
              <span key={idx} className="cert-chip">
                <FiCheckCircle className="cert-check" aria-hidden="true" />
                <span>{cert}</span>
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}