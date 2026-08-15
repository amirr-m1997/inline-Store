import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const read = (file: string) => fs.readFileSync(path.resolve(process.cwd(), file), "utf8");

describe("technical resources foundation", () => {
  it("keeps the resource index server-rendered, empty-safe, and noindexable when empty", () => {
    const source = read("app/[locale]/resources/page.tsx");
    expect(source).toContain("getProductDocumentsServer");
    expect(source).toContain("resources.length ?");
    expect(source).toContain("index: false");
    expect(source).toContain("localizedAlternates");
    expect(source).toContain("documentTypeLabel");
    expect(source).toContain("resource-metadata");
    expect(source).toContain("Download");
  });

  it("maps published API documents into the existing PDP document shape", () => {
    const source = read("lib/product/adapters.ts");
    expect(source).toContain("raw.documents || []");
    expect(source).toContain("fileUrl:document.file_url");
    expect(source).toContain("fileName:document.file_name");
  });
});
