const icon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#c62b35"/><path fill="#fff" d="M19 46V18h11c9 0 15 5 15 14s-6 14-15 14H19Zm9-8h2c4 0 7-2 7-6s-3-6-7-6h-2v12Z"/></svg>`;

export function GET() {
  return new Response(icon, {
    headers: {
      "Content-Type": "image/svg+xml",
      "Cache-Control": "public, max-age=86400",
    },
  });
}
