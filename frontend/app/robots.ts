import type { MetadataRoute } from "next";
import { absoluteUrl } from "../lib/locale-url";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [{ userAgent: "*", allow: ["/fa", "/en", "/fa/", "/en/"], disallow: ["/api/", "/media/", "/admin/", "/fa/account", "/en/account", "/fa/cart", "/en/cart", "/fa/checkout", "/en/checkout", "/fa/payment", "/en/payment", "/fa/login", "/en/login", "/fa/register", "/en/register", "/fa/forgot-password", "/en/forgot-password", "/fa/reset-password", "/en/reset-password"] }], sitemap: absoluteUrl("/sitemap.xml"), host: absoluteUrl("/") , };
}
