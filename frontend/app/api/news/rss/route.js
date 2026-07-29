import { API_URL } from "../../../../lib/api";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const response = await fetch(`${API_URL}/api/news/rss`, {
      cache: "no-store",
      headers: {
        Accept: "application/rss+xml, application/xml;q=0.9",
      },
    });

    if (!response.ok) {
      return new Response("RSS vaqtincha mavjud emas", { status: 502 });
    }

    const xml = await response.text();
    return new Response(xml, {
      headers: {
        "Content-Type": "application/rss+xml; charset=utf-8",
        "Cache-Control": "public, s-maxage=900, stale-while-revalidate=3600",
      },
    });
  } catch {
    return new Response("RSS vaqtincha mavjud emas", { status: 502 });
  }
}
