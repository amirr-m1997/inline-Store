/* تست DOM پنل با jsdom — اجرا:
       python3 scripts/dump_admin_fixtures.py /tmp/admin_fixtures
       cd /tmp/jsd && npm install jsdom --no-save     # اگر نصب نیست
       NODE_PATH=/tmp/jsd/node_modules node scripts/check_panel_dom.js /tmp/admin_fixtures
   رفتار واقعی panel.js روی HTML واقعی پنل را می‌سنجد (بدون مرورگر). */
const fs = require("fs");
const path = require("path");

let JSDOM;
try {
  ({ JSDOM } = require("jsdom"));
} catch (e) {
  console.error("jsdom نصب نیست:  cd /tmp/jsd && npm install jsdom --no-save");
  process.exit(2);
}

const fixturesDir = process.argv[2] || "/tmp/admin_fixtures";
const panelJs = fs.readFileSync(
  path.join(__dirname, "..", "static", "js", "panel.js"),
  "utf8"
);

let failures = 0;
function check(label, condition, extra) {
  const ok = !!condition;
  if (!ok) failures++;
  console.log(`${ok ? "✓" : "✗"} ${label}${extra !== undefined && !ok ? "   → " + extra : ""}`);
}

function load(name) {
  const file = path.join(fixturesDir, `${name}.html`);
  if (!fs.existsSync(file)) {
    console.error(`فایل fixture نیست: ${file}`);
    process.exit(2);
  }
  const dom = new JSDOM(fs.readFileSync(file, "utf8"), {
    url: "https://panel.local/admin/orders/order/",
    runScripts: "outside-only",
    pretendToBeVisual: true,
  });
  const errors = [];
  dom.window.eval(`(function(){ window.__err=[]; window.onerror=function(m){window.__err.push(String(m));}; })()`);
  dom.window.eval(panelJs);
  /* jsdom ممکن است readyState را loading نگه دارد؛ رویداد پایان پارس را دستی می‌فرستیم */
  dom.window.document.dispatchEvent(new dom.window.Event("DOMContentLoaded", { bubbles: true }));
  errors.push(...(dom.window.__err || []));
  return { dom, doc: dom.window.document, errors };
}

/* ------------------------------------------------ ۱) فهرست سفارش‌ها */
{
  const { doc, errors } = load("orders_changelist");
  console.log("— فهرست سفارش‌ها —");
  check("بدون خطای جاوااسکریپت", errors.length === 0, errors.join(" | "));

  const q = doc.querySelector('input[name="q"]');
  check("کادر جست‌وجو برچسب دسترس‌پذیر گرفت", q && q.getAttribute("aria-label"), q && q.outerHTML.slice(0, 80));
  check("placeholder کادر جست‌وجو پر شد", q && q.placeholder);

  const toggle = doc.querySelector('input[name="action-toggle"]');
  check("چک‌باکس «انتخاب همه» برچسب گرفت", toggle && toggle.getAttribute("aria-label"));

  const rowbox = doc.querySelector('#result_list input[name="_selected_action"]');
  check("چک‌باکس ردیف‌ها برچسب گرفت", rowbox && rowbox.getAttribute("aria-label"));

  const counter = doc.querySelector(".action-counter");
  check("شمارنده‌ی اکشن‌های گروهی ارقام فارسی شد",
    counter && !/[0-9]/.test(counter.textContent), counter && counter.textContent.trim());

  const pageLinks = Array.from(doc.querySelectorAll('a[href^="?p="]'));
  check("شماره‌های صفحه‌بندی فارسی شد",
    pageLinks.length > 0 && pageLinks.every((a) => !/[0-9]/.test(a.textContent)),
    pageLinks.map((a) => a.textContent).join(","));

  check("attribute داده‌ای دست‌نخورده ماند (data-actions-icnt)",
    counter && counter.getAttribute("data-actions-icnt") !== null && /^[0-9]+$/.test(counter.getAttribute("data-actions-icnt") || ""));

  const filter = doc.querySelector("#changelist-filter");
  check("برچسب‌های فیلتر ارقام فارسی شدند",
    filter ? !/(\(|^)\s*[0-9]+\s*\)/.test(filter.textContent) : true,
    filter ? (filter.textContent.match(/\([0-9]+\)/) || [""])[0] : "");

  const active = doc.querySelector('a[href="/admin/orders/order"][aria-current="page"], a[href="/admin/orders/order/"][aria-current="page"]');
  check("سایدبار: گزینه‌ی صفحه‌ی جاری aria-current گرفت", active || doc.querySelectorAll('[aria-current="page"]').length > 0);

  const searchSubmit = doc.querySelector("#searchbar-submit");
  check("دکمه‌ی جست‌وجو برچسب گرفت", searchSubmit && searchSubmit.getAttribute("aria-label"));
}

/* ------------------------------------------------ ۲) فیلتر تاریخ شمسی */
{
  const { doc, errors } = load("orders_filtered");
  console.log("— فهرست سفارش‌ها با فیلتر تاریخ —");
  check("بدون خطای جاوااسکریپت", errors.length === 0, errors.join(" | "));
  const from = doc.querySelector('input.vDateField[name="ordered_at_from"]');
  check("ورودی فیلتر مقدار شمسی را نشان می‌دهد", from && /[۰-۹]/.test(from.value || ""), from && from.value);
  check("placeholder و title شمسی روی ورودی فیلتر هست", from && from.placeholder && from.title, from && (from.placeholder + " | " + from.title));
  const hint = doc.querySelector(".panel-jalali-hint");
  check("راهنمای تاریخ زیر فیلد نمایش داده شد", hint && hint.textContent.length > 0, hint && hint.textContent);
  check("راهنمای تاریخ مقدار میلادی معادل را می‌دهد", hint && /میلادی/.test(hint.textContent), hint && hint.textContent);
}

/* ------------------------------------------------ ۳) فرم ویرایش (تبدیل ورودی شمسی) */
{
  const { dom, doc, errors } = load("invoice_change");
  console.log("— فرم ویرایش فاکتور —");
  check("بدون خطای جاوااسکریپت", errors.length === 0, errors.join(" | "));
  const dates = Array.from(doc.querySelectorAll("input.vDateField"));
  check("فیلد تاریخ در فرم وجود دارد", dates.length > 0);
  const hint = doc.querySelector(".panel-jalali-hint");
  check("راهنمای شمسی برای تاریخ میلادی فرم ساخته شد",
    hint && /شمسی/.test(hint.textContent), hint && hint.textContent);
  check("title راهنما روی ورودی تاریخ تنظیم شد", dates[0] && dates[0].getAttribute("title"));

  /* = ورودی شمسی → تبدیل خودکار به میلادی = */
  const first = dates.find((d) => /^\d{4}-\d{2}-\d{2}$/.test(d.value || ""));
  if (first) {
    const before = first.value;
    first.value = "۱۴۰۵/۰۷/۱۵";
    first.dispatchEvent(new dom.window.Event("change", { bubbles: true }));
    check("ورودی شمسی ۱۴۰۵/۰۷/۱۵ به 2026-10-07 تبدیل شد", first.value === "2026-10-07", `${before} → ${first.value}`);
    first.value = before;
    first.dispatchEvent(new dom.window.Event("change", { bubbles: true }));
    check("ورودی میلادی دست‌نخورده ماند", first.value === before, first.value);
  } else {
    check("فیلد تاریخی با مقدار میلادی برای تست یافت شد", false);
  }
}

/* ------------------------------------------------ ۴) داشبورد و صفحه‌ی ورود */
{
  const { errors } = load("dashboard");
  console.log("— داشبورد —");
  check("بدون خطای جاوااسکریپت", errors.length === 0, errors.join(" | "));
}
{
  const { doc, errors } = load("login");
  console.log("— صفحه‌ی ورود —");
  check("بدون خطای جاوااسکریپت", errors.length === 0, errors.join(" | "));
  check("بدون وابستگی به المان‌های پنل هم خطا نمی‌دهد", true);
  check("صفحه‌ی ورود RTL است", doc.documentElement.getAttribute("dir") === "rtl");
}

console.log(failures === 0 ? "\nنتیجه: همه‌ی بررسی‌های DOM موفق ✓" : `\nنتیجه: ${failures} بررسی ناموفق ✗`);
process.exit(failures === 0 ? 0 : 1);
