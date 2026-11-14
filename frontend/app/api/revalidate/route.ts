import { NextRequest, NextResponse } from "next/server";
import { revalidatePath, revalidateTag } from "next/cache";

export async function POST(request: NextRequest) {
  const secret = request.headers.get("x-revalidate-secret") || request.nextUrl.searchParams.get("secret");
  const expectedSecret = process.env.REVALIDATION_SECRET || "mehrasl-cache-secret-2026";

  if (secret !== expectedSecret) {
    return NextResponse.json({ detail: "Unauthorized revalidation request." }, { status: 401 });
  }

  try {
    const body = await request.json().catch(() => ({}));
    const tag = body.tag || request.nextUrl.searchParams.get("tag");
    const path = body.path || request.nextUrl.searchParams.get("path");

    const revalidated: string[] = [];

    if (tag) {
      revalidateTag(tag, { expire: 0 });
      revalidated.push(`tag:${tag}`);
    }

    if (path) {
      revalidatePath(path);
      revalidated.push(`path:${path}`);
    }

    if (!tag && !path) {
      revalidateTag("catalog", { expire: 0 });
      revalidateTag("products", { expire: 0 });
      revalidatePath("/[locale]/shop", "page");
      revalidatePath("/[locale]", "page");
      revalidated.push("catalog", "products", "shop", "homepage");
    }

    return NextResponse.json({ revalidated, timestamp: Date.now() });
  } catch (error) {
    return NextResponse.json({ detail: "Failed to revalidate cache.", error: String(error) }, { status: 500 });
  }
}
