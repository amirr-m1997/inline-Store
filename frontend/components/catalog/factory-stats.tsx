import { FiAward, FiShield, FiTrendingUp, FiMapPin, FiCheckCircle } from "react-icons/fi";
import type { CompanyStatItem } from "../../lib/api/content";
import type { CompanyCertification } from "./trust-sections";

interface FactoryStatsProps {
  locale?: string;
  stats?: CompanyStatItem[];
  certifications?: CompanyCertification[];
}

export function FactoryStats({ locale = "fa", stats = [], certifications = [] }: FactoryStatsProps) {
  const english = locale === "en";

  if (!stats.length && !certifications.length) {
    return null;
  }

  const iconMap: Record<string, typeof FiAward> = {
    award: FiAward,
    "trending-up": FiTrendingUp,
    shield: FiShield,
    "map-pin": FiMapPin,
  };

  const liveCertifications = certifications
    .filter((c) => !c.title_fa.startsWith("[DEMO]"))
    .slice(0, 4);

  return (
    <section className="enterprise-section site-container factory-stats-wrap" aria-labelledby="stats-heading">
      <div className="factory-stats-card">
        <header className="factory-stats-header">
          <span className="stats-tag">
            {english ? "Manufacturing Heritage & Scale" : "افتخارات، توانمندی و سابقه صنعتی"}
          </span>
          <h2 id="stats-heading" className="stats-title">
            {english ? "Decades of Industrial Engineering & National Scale" : "پیشرو در طراحی و تولید تأسیسات سرمایشی و پروژه‌های ملی"}
          </h2>
          <p className="stats-subtitle">
            {english
              ? "Driven by engineering excellence, heavy-duty production infrastructure and nationwide service reliability."
              : "تکیه بر مهندسی بومی، خطوط تولید مکانیزه، استانداردهای بین‌المللی و پشتیبانی فنی در سخت‌ترین شرایط اقلیمی."}
          </p>
        </header>

        {/* Dynamic Stats Grid loaded from server */}
        {stats.length > 0 && (
          <div className="factory-stats-grid">
            {stats.map((stat) => {
              const Icon = iconMap[stat.icon] || FiAward;
              const value = english && stat.value_en ? stat.value_en : stat.value_fa;
              const label = english && stat.label_en ? stat.label_en : stat.label_fa;
              const desc = english && stat.description_en ? stat.description_en : stat.description_fa;

              return (
                <div key={stat.id} className="factory-stat-item">
                  <div className="stat-icon-box">
                    <Icon aria-hidden="true" />
                  </div>
                  <div className="stat-value">
                    <bdi>{value}</bdi>
                  </div>
                  <h3 className="stat-label">{label}</h3>
                  {desc && <p className="stat-desc">{desc}</p>}
                </div>
              );
            })}
          </div>
        )}

        {/* Dynamic Certifications Chips from server */}
        {liveCertifications.length > 0 && (
          <div className="factory-certs-footer">
            <span className="certs-heading">
              {english ? "Certified Accreditations & Standards:" : "گواهینامه‌ها و استانداردهای اخذشده:"}
            </span>
            <div className="certs-pills">
              {liveCertifications.map((cert) => (
                <span key={cert.id} className="cert-pill" title={cert.issuer || cert.title_fa}>
                  <FiCheckCircle className="cert-check-icon" aria-hidden="true" />
                  <span>{cert.title_fa}</span>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}