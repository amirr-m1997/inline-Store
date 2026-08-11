export type ApiRoot = { version: string; status: string; resources: Record<string, string> };
const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export async function getApiRoot(): Promise<ApiRoot> {
  const response = await fetch(`${baseUrl}/api/v1/`, { next: { revalidate: 60 } });
  if (!response.ok) throw new Error("Unable to reach API");
  return response.json() as Promise<ApiRoot>;
}

