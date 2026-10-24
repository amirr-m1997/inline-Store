"use client";

export function BackToTop({ english, floating = false }: { english: boolean; floating?: boolean }) {
  return (
    <button
      className={floating ? "floating-actions-top" : "footer-back-to-top"}
      type="button"
      aria-label={english ? "Back to top" : "بازگشت به بالا"}
      onClick={() => {
        const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
      }}
    >
      {floating ? <span aria-hidden="true">↑</span> : <><span>{english ? "Back to top" : "بازگشت به بالا"}</span><span aria-hidden="true">↑</span></>}
    </button>
  );
}
