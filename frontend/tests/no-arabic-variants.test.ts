import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

// Unsafe Arabic code points that must never ship to the browser.
// ئ (U+0626), ؤ (U+0624), أ (U+0623) and إ (U+0625) are intentionally
// excluded: they are correct Persian orthography.
const ARABIC_VARIANTS = new RegExp(
  "[\\u{643}\\u{64A}\\u{649}\\u{629}\\u{660}-\\u{669}\\u{640}]",
  "u",
);

const ROOTS = ["app", "components", "lib", "types", "services", "hooks"];
const EXTENSIONS = [".ts", ".tsx", ".css", ".mjs"];

function collectFiles(dir: string, out: string[] = []): string[] {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === "node_modules" || entry.name === ".next") continue;
    const full = join(dir, entry.name);
    if (entry.isDirectory()) collectFiles(full, out);
    else if (EXTENSIONS.some((ext) => entry.name.endsWith(ext))) out.push(full);
  }
  return out;
}

describe("no unsafe Arabic variants in shipped source", () => {
  it("contains only Persian forms (backend normalizes data, source must be clean)", () => {
    const root = join(process.cwd());
    const offenders: string[] = [];
    for (const base of ROOTS) {
      try {
        if (!statSync(join(root, base)).isDirectory()) continue;
      } catch {
        continue;
      }
      for (const file of collectFiles(join(root, base))) {
        if (ARABIC_VARIANTS.test(readFileSync(file, "utf8"))) offenders.push(file);
      }
    }
    expect(offenders).toEqual([]);
  });
});
