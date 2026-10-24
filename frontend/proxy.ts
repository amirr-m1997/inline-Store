import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

// English storefront is temporarily disabled: every entry point lands on
// Persian. Re-enable by restoring the accept-language negotiation.
export function proxy(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  if (pathname === "/en" || pathname.startsWith("/en/")) {
    const faPath = pathname.replace(/^\/en(?=\/|$)/, "/fa");
    return NextResponse.redirect(new URL(faPath + request.nextUrl.search, request.url));
  }
  if (pathname === "/") {
    return NextResponse.redirect(new URL("/fa", request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/", "/en", "/en/:path*"],
};
