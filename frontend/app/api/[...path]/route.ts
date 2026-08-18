import { NextRequest } from "next/server";

const backendUrl = process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type RouteContext = { params: Promise<{ path: string[] }> };

async function proxy(request: NextRequest, { params }: RouteContext) {
  if (!backendUrl) {
    return Response.json({ detail: "API URL is not configured." }, { status: 500 });
  }

  const { path } = await params;
  const target = new URL(`/api/${path.join("/")}/`, backendUrl);
  target.search = request.nextUrl.search;

  const headers = new Headers({ Accept: "application/json" });
  for (const name of ["Authorization", "X-Guest-Token", "Content-Type", "Cookie", "X-CSRFToken", "Origin", "Referer"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }

  const hasBody = ["POST", "PATCH", "PUT"].includes(request.method);
  try {
    const upstream = await fetch(target, {
      method: request.method,
      cache: "no-store",
      headers,
      body: hasBody ? await request.arrayBuffer() : undefined,
    });
    const responseHeaders = new Headers({ "Content-Type": upstream.headers.get("Content-Type") ?? "application/json" });
    for (const name of ["Content-Disposition", "Content-Length"]) {
      const value = upstream.headers.get(name);
      if (value) responseHeaders.set(name, value);
    }
    const setCookie = upstream.headers.get("Set-Cookie");
    if (setCookie) responseHeaders.set("Set-Cookie", setCookie);
    return new Response(upstream.body, {
      status: upstream.status,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error(`Unable to reach backend API at ${target.origin}`, error);
    return Response.json({ detail: "Unable to reach the API service.", target: target.origin }, { status: 502 });
  }
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
export const PUT = proxy;
export const DELETE = proxy;
