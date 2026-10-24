"use client";

export function BackToBottom({ english }: { english: boolean }) {
  return (
    <button
      className="floating-actions-bottom"
      type="button"
      aria-label={english ? "Go to bottom" : "رفتن به پایین صفحه"}
      onClick={() => {
        const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        window.scrollTo({
          top: document.documentElement.scrollHeight,
          behavior: reduceMotion ? "auto" : "smooth",
        });
      }}
    >
      <span aria-hidden="true">↓</span>
    </button>
  );
}
