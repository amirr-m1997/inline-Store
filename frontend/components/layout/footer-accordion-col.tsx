"use client";

import { useState } from "react";
import Link from "next/link";
import { FiChevronLeft, FiChevronDown } from "react-icons/fi";

export type FooterLink = { id?: string | number; label: string; href: string; external?: boolean; newTab?: boolean };

export function FooterAccordionCol({
  title,
  id,
  links,
  english,
}: {
  title: string;
  id: string;
  links: FooterLink[];
  english?: boolean;
}) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <section className={`footer-col footer-col-accordion${isOpen ? " is-open" : ""}`} aria-labelledby={id}>
      <button
        type="button"
        className="footer-accordion-header"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-expanded={isOpen}
      >
        <h2 className="footer-col-title" id={id}>
          {title}
        </h2>
        <span className="footer-accordion-toggle" aria-hidden="true">
          <FiChevronDown size={18} className={`accordion-icon${isOpen ? " rotated" : ""}`} />
        </span>
      </button>

      <nav
        aria-label={english ? title : title}
        className={`footer-nav-collapse${isOpen ? " is-expanded" : ""}`}
      >
        <ul className="footer-nav-list">
          {links.map((link, index) => {
            const key = link.id ? `link-${link.id}` : `link-${link.href}-${index}`;
            return (
              <li key={key}>
                {link.external ? (
                  <a
                    href={link.href}
                    target={link.newTab ? "_blank" : undefined}
                    rel={link.newTab ? "noreferrer" : undefined}
                  >
                    <FiChevronLeft size={13} className="footer-link-icon" aria-hidden="true" />
                    <span>{link.label}</span>
                  </a>
                ) : (
                  <Link href={link.href}>
                    <FiChevronLeft size={13} className="footer-link-icon" aria-hidden="true" />
                    <span>{link.label}</span>
                  </Link>
                )}
              </li>
            );
          })}
        </ul>
      </nav>
    </section>
  );
}
