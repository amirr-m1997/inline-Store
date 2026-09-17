import type { NextRequest } from "next/server";

const backendUrl = process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
type RouteContext = { params: Promise<{ path: string[] }> };

export async function GET(request: NextRequest, { params }: RouteContext) {
  const { path } = await params;
  const target = new URL(`/media/${path.map(encodeURIComponent).join("/")}`, backendUrl);
  try {
    const forwardHeaders = new Headers();
    const range = request.headers.get("Range");
    if (range) forwardHeaders.set("Range", range);
    const ifNoneMatch = request.headers.get("If-None-Match");
    if (ifNoneMatch) forwardHeaders.set("If-None-Match", ifNoneMatch);
    const ifModifiedSince = request.headers.get("If-Modified-Since");
    if (ifModifiedSince) forwardHeaders.set("If-Modified-Since", ifModifiedSince);
    const upstream = await fetch(target, { cache: "no-store", headers: forwardHeaders });
    if (upstream.status === 304) return new Response(null, { status: 304 });
    if (!upstream.ok) return new Response(null, { status: upstream.status });
    const headers = new Headers();
    for (const name of ["Content-Type", "Content-Length", "Content-Range", "Accept-Ranges", "Last-Modified", "ETag"]) {
      const value = upstream.headers.get(name); if (value) headers.set(name, value);
    }
    headers.set("Cache-Control", "public, max-age=3600, stale-while-revalidate=86400");
    return new Response(upstream.body, { status: upstream.status, headers });
  } catch {
    return new Response(null, { status: 502 });
  }
}
