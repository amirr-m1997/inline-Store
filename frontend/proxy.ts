import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

export function proxy(request: NextRequest) {
  const cookieLocale = request.cookies.get("NEXT_LOCALE")?.value;
  const accepted = request.headers.get("accept-language") || "";
  const prefersEn = /en/i.test(cookieLocale || "") || (/en/i.test(accepted) && !/fa/i.test(accepted.split(",")[0] || ""));
  return NextResponse.redirect(new URL(prefersEn ? "/en" : "/fa", request.url));
}

export const config = {
  matcher: "/",
};
