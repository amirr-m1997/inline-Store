import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const read = (file: string) => fs.readFileSync(path.resolve(process.cwd(), file), "utf8");

describe("technical resources foundation", () => {
  it("keeps the resource index server-rendered, indexable, and empty-safe", () => {
    const source = read("app/[locale]/resources/page.tsx");
    expect(source).toContain("getProductDocumentsServer");
    expect(source).toContain("page.results.length ?");
    expect(source).toContain("index: true");
    expect(source).toContain("localizedAlternates");
    expect(source).toContain("documentTypeLabel");
    expect(source).toContain("resource-metadata");
    expect(source).toContain("Download");
    expect(source).toContain("resource-filters");
    expect(source).toContain("page_size");
  });

  it("keeps the legacy support resources route compatible and uses the shared event architecture", () => {
    const legacy = read("app/[locale]/support/resources/page.tsx");
    const events = read("app/[locale]/events/page.tsx");
    expect(legacy).toContain("permanentRedirect");
    expect(legacy).toContain("/${locale}/resources");
    expect(events).toContain('content_type: "event"');
    expect(events).toContain("EditorialCard");
  });

  it("maps published API documents into the existing PDP document shape", () => {
    const source = read("lib/product/adapters.ts");
    expect(source).toContain("raw.documents || []");
    expect(source).toContain("fileUrl:document.file_url");
    expect(source).toContain("fileName:document.file_name");
  });
});
