import fs from "node:fs";

const root = ".next";
const budgets = { homepage: 60_000, catalog: 85_000, category: 85_000, pdp: 80_000 };
const manifests = { homepage: "server/app/[locale]/page_client-reference-manifest.js", catalog: "server/app/[locale]/shop/page_client-reference-manifest.js", category: "server/app/[locale]/category/[slug]/page_client-reference-manifest.js", pdp: "server/app/[locale]/product/[slug]/page_client-reference-manifest.js" };
function routeBytes(file) {
  const source = fs.readFileSync(`${root}/${file}`, "utf8");
  const manifest = JSON.parse(source.slice(source.indexOf("= {") + 2, source.lastIndexOf(";")));
  const chunks = new Set();
  for (const entry of Object.values(manifest.clientModules || {})) for (const chunk of entry.chunks || []) chunks.add(chunk.replace("/_next/", ""));
  return [...chunks].reduce((total, chunk) => total + fs.statSync(`${root}/${chunk}`).size, 0);
}
function filesUnder(directory) { if (!fs.existsSync(directory)) return []; return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => entry.isDirectory() ? filesUnder(`${directory}/${entry.name}`) : [`${directory}/${entry.name}`]); }
const manifestFiles = filesUnder(`${root}/server`).filter((file) => file.endsWith("client-reference-manifest.js"));
const css = filesUnder(`${root}/static`).filter((file) => file.endsWith(".css")).reduce((total, file) => total + fs.statSync(file).size, 0);
let failed = false;
for (const [route, file] of Object.entries(manifests)) { const candidates = manifestFiles.filter((candidate) => candidate.includes(route === "homepage" ? "/[locale]/page" : route === "catalog" ? "/shop/" : route === "category" ? "/category/" : "/product/")); const selected = candidates[0] || file; if (!fs.existsSync(`${root}/${selected}`)) { console.error(`Missing build manifest for ${route}. Run next build first.`); failed = true; continue; } const bytes = routeBytes(selected.replace(`${root}/`, "")); console.log(`${route}: ${(bytes / 1024).toFixed(1)} KiB JS (budget ${(budgets[route] / 1024).toFixed(1)} KiB)`); if (bytes > budgets[route]) failed = true; }
console.log(`global CSS: ${(css / 1024).toFixed(1)} KiB (soft budget 180.0 KiB)`);
if (css > 180_000) failed = true;
if (failed) { console.error("Performance budget exceeded."); process.exit(1); }
