"use client";

import type { ReactNode } from "react";
import { useEffect, useRef, useState } from "react";

export function ProductTabs({ description, specifications }: { description: string; specifications: ReactNode }) {
  const [activeTab, setActiveTab] = useState<"specs" | "description">("specs");
  const tabs = [{ id: "specs", label: "مشخصات فنی", enabled: true }, ...(description ? [{ id: "description", label: "معرفی محصول", enabled: true }] : [])];
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const select = (id: "specs" | "description") => setActiveTab(id);
  const move = (index: number) => { const next = (index + tabs.length) % tabs.length; select(tabs[next].id as "specs" | "description"); tabRefs.current[next]?.focus(); };
  return <section className="product-detail-tabs"><div className="product-tab-list" role="tablist" aria-label="اطلاعات محصول" onKeyDown={(event) => { const index = tabs.findIndex((tab) => tab.id === activeTab); if (event.key === "ArrowRight" || event.key === "ArrowDown") { event.preventDefault(); move(index + 1); } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") { event.preventDefault(); move(index - 1); } else if (event.key === "Home") { event.preventDefault(); move(0); } else if (event.key === "End") { event.preventDefault(); move(tabs.length - 1); } }}>
    {tabs.map((tab, index) => <button ref={(element) => { tabRefs.current[index] = element; }} key={tab.id} type="button" role="tab" id={`product-tab-${tab.id}`} aria-controls={`product-panel-${tab.id}`} aria-selected={activeTab === tab.id} tabIndex={activeTab === tab.id ? 0 : -1} onClick={() => select(tab.id as "specs" | "description")}>{tab.label}</button>)}
    <button className="future-tab" type="button" role="tab" id="product-tab-reviews" aria-controls="product-panel-reviews" aria-selected="false" tabIndex={-1} disabled>نظرات <small>به‌زودی</small></button><button className="future-tab" type="button" role="tab" id="product-tab-questions" aria-controls="product-panel-questions" aria-selected="false" tabIndex={-1} disabled>پرسش و پاسخ <small>به‌زودی</small></button>
  </div>{activeTab === "specs" ? <div id="product-panel-specs" role="tabpanel" aria-labelledby="product-tab-specs" tabIndex={0}>{specifications}</div> : <div id="product-panel-description" role="tabpanel" aria-labelledby="product-tab-description" tabIndex={0}><p>{description}</p></div>}</section>;
}
