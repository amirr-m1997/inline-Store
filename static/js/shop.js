/* ============================================================================
   فروشگاه مهراصل — رفتارهای سمت مرورگر
   ۱) کلید تم روشن/تیره با ذخیره‌سازی در مرورگر
   ۲) شمارندهٔ تعداد (+/-) در فرم‌های افزودن به سبد
   ۳) تأیید پیش از حذف و تنظیم خودکار فیلترها
   نکته: سایت بدون جاوااسکریپت هم کار می‌کند (همهٔ فرم‌ها معمولی هستند).
   ========================================================================== */
(function () {
  "use strict";

  var THEME_KEY = "mehrasl-shop-theme";

  /* ---------------------------------------------------------------- تم */
  function currentTheme() {
    var attr = document.documentElement.getAttribute("data-theme");
    if (attr === "light" || attr === "dark") return attr;
    var saved = null;
    try { saved = localStorage.getItem(THEME_KEY); } catch (e) { saved = null; }
    if (saved === "light" || saved === "dark") return saved;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
      var isDark = theme === "dark";
      /* آیکون و متن با CSS بر پایهٔ data-theme جابه‌جا می‌شوند (بدون وابستگی به فونت آیکون) */
      btn.setAttribute("aria-label", isDark ? "تغییر به حالت روشن" : "تغییر به حالت تیره");
      btn.setAttribute("title", isDark ? "حالت روشن" : "حالت تیره");
    });
  }

  function wireTheme() {
    applyTheme(currentTheme());
    document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
        try { localStorage.setItem(THEME_KEY, next); } catch (e) { /* حالت خصوصی مرورگر */ }
        applyTheme(next);
      });
    });
  }

  /* -------------------------------------------------------------- شمارنده */
  function wireQty() {
    document.querySelectorAll(".qty").forEach(function (box) {
      var input = box.querySelector("input");
      if (!input) return;
      var step = parseFloat(input.getAttribute("step") || "1") || 1;
      var min = parseFloat(input.getAttribute("min") || "0") || 0;
      box.querySelectorAll("button[data-delta]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var delta = parseFloat(btn.getAttribute("data-delta")) || 0;
          var value = parseFloat((input.value || "0").replace(/[۰-۹]/g, function (d) {
            return "۰۱۲۳۴۵۶۷۸۹".indexOf(d);
          })) || 0;
          value = Math.max(min, value + delta * step);
          input.value = value;
          input.dispatchEvent(new Event("change", { bubbles: true }));
        });
      });
    });
  }

  /* ------------------------------------------------------------ فیلترها */
  function wireFilters() {
    document.querySelectorAll("[data-auto-submit]").forEach(function (el) {
      el.addEventListener("change", function () {
        if (el.form) el.form.submit();
      });
    });
    document.querySelectorAll("[data-confirm]").forEach(function (el) {
      el.addEventListener("submit", function (event) {
        if (!window.confirm(el.getAttribute("data-confirm"))) event.preventDefault();
      });
      if (el.tagName === "A" || el.tagName === "BUTTON") {
        el.addEventListener("click", function (event) {
          if (!window.confirm(el.getAttribute("data-confirm"))) event.preventDefault();
        });
      }
    });
  }

  function boot() {
    try {
      wireTheme();
      wireQty();
      wireFilters();
    } catch (e) {
      if (window.console && console.warn) console.warn("shop.js:", e);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
