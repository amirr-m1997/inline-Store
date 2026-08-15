import { permanentRedirect } from "next/navigation";

export default async function LegacyResourcesRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  permanentRedirect(`/${locale}/resources`);
}
