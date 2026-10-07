/* تست الگوریتم‌های panel.js بدون مرورگر — اجرا:  node scripts/check_panel_js.js
   صحت تبدیل تاریخ شمسی/میلادی و تفسیر ورودی کاربر را بررسی می‌کند. */
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const file = path.join(__dirname, "..", "static", "js", "panel.js");
let src = fs.readFileSync(file, "utf8");
src = src.replace(
  /\}\)\(\);\s*$/,
  "  globalThis.__panel = { gregorianToJalali, jalaliToGregorian, normaliseDateValue, toFa, toEn };\n})();\n"
);

const stubEl = {
  setAttribute() {},
  getAttribute() {
    return null;
  },
  addEventListener() {},
  insertAdjacentElement() {},
  closest() {
    return null;
  },
  querySelector() {
    return null;
  },
  createElement() {
    return { classList: { add() {} }, style: {} };
  },
};
const document = {
  readyState: "complete",
  addEventListener() {},
  querySelectorAll() {
    return [];
  },
  createElement() {
    return Object.assign({}, stubEl);
  },
};
const sandbox = { document, console, location: { pathname: "/admin/" }, window: {} };
vm.createContext(sandbox);
vm.runInContext(src, sandbox);

const api = sandbox.__panel;
let failures = 0;
function check(label, actual, expected) {
  const a = JSON.stringify(actual);
  const e = JSON.stringify(expected);
  const ok = a === e;
  if (!ok) failures++;
  console.log(`${ok ? "✓" : "✗"} ${label}  →  ${a}${ok ? "" : "   (انتظار: " + e + ")"}`);
}

console.log("— تبدیل میلادی → شمسی → میلادی —");
[
  [2026, 10, 7, [1405, 7, 15]],
  [2026, 3, 21, [1405, 1, 1]],
  [2025, 3, 21, [1404, 1, 1]],
  [2024, 3, 20, [1403, 1, 1]],
  [2027, 3, 21, [1406, 1, 1]],
].forEach(([y, m, d, expected]) => {
  const j = api.gregorianToJalali(y, m, d);
  check(`${y}-${m}-${d} → شمسی`, j, expected);
  check(`  برگشت به میلادی`, api.jalaliToGregorian(j[0], j[1], j[2]), [y, m, d]);
});

console.log("— تفسیر ورودی کاربر —");
check("۱۴۰۵/۰۷/۱۵ (فارسی)", api.normaliseDateValue("۱۴۰۵/۰۷/۱۵"), [2026, 10, 7]);
check("1405-7-15", api.normaliseDateValue("1405-7-15"), [2026, 10, 7]);
check("1405.07.15", api.normaliseDateValue("1405.07.15"), [2026, 10, 7]);
check("14050715", api.normaliseDateValue("14050715"), [2026, 10, 7]);
check("2026-04-05 (میلادی)", api.normaliseDateValue("2026-04-05"), [2026, 4, 5]);
check("۱۴۰۵/۱۳/۴۰ (نامعتبر)", api.normaliseDateValue("۱۴۰۵/۱۳/۴۰"), null);
check("abc (نامعتبر)", api.normaliseDateValue("abc"), null);
check("خالی", api.normaliseDateValue(""), null);
check("ارقام: toFa(1405)", api.toFa(1405), "۱۴۰۵");
check("ارقام: toEn(۱۴۰۵)", api.toEn("۱۴۰۵"), "1405");
check("ارقام عربی: toEn(١٤٠٥)", api.toEn("١٤٠٥"), "1405");

console.log(failures === 0 ? "\nنتیجه: همه‌ی بررسی‌ها موفق ✓" : `\nنتیجه: ${failures} بررسی ناموفق ✗`);
process.exit(failures === 0 ? 0 : 1);
