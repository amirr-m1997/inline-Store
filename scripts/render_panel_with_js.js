/* اجرای panel.js روی HTML واقعی پنل و ذخیره‌ی نتیجه‌ی نهایی (همان چیزی که مرورگر می‌سازد).
   استفاده:  NODE_PATH=/tmp/jsd/node_modules node scripts/render_panel_with_js.js <in> <out> */
const fs = require("fs");
const path = require("path");

let JSDOM;
try {
  ({ JSDOM } = require("jsdom"));
} catch (e) {
  console.error("jsdom نصب نیست");
  process.exit(2);
}

const inDir = process.argv[2];
const outDir = process.argv[3];
const panelJs = fs.readFileSync(path.join(__dirname, "..", "static", "js", "panel.js"), "utf8");
fs.mkdirSync(outDir, { recursive: true });

for (const file of fs.readdirSync(inDir).filter((f) => f.endsWith(".html"))) {
  const dom = new JSDOM(fs.readFileSync(path.join(inDir, file), "utf8"), {
    url: "https://panel.local/admin/",
    runScripts: "outside-only",
    pretendToBeVisual: true,
  });
  dom.window.eval(`(function(){window.__err=[];window.onerror=function(m){window.__err.push(String(m));};})()`);
  dom.window.eval(panelJs);
  dom.window.document.dispatchEvent(new dom.window.Event("DOMContentLoaded", { bubbles: true }));
  const errors = dom.window.__err || [];
  fs.writeFileSync(path.join(outDir, file), dom.serialize(), "utf8");
  const actions = dom.window.document.querySelectorAll(".panel-row-actions").length;
  const skip = dom.window.document.getElementById("panel-skip-link") ? 1 : 0;
  console.log(
    `${errors.length ? "✗" : "✓"} ${file.padEnd(26)} کنش درون‌ردیفی: ${String(actions).padStart(3)} | پیوند پرش: ${skip}` +
      (errors.length ? ` | خطا: ${errors.join(" | ")}` : "")
  );
}
