import { API_URL } from "../../lib/api";
import { SITE_NAME, SITE_URL } from "../../lib/site";

const NEWS_WINDOW_MS = 48 * 60 * 60 * 1000;

function escapeXml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

export async function GET() {
  let articles = [];

  try {
    let response = await fetch(`${API_URL}/api/news/sitemap?hours=48`, {
      next: { revalidate: 900 },
    });
    if (!response.ok) {
      response = await fetch(`${API_URL}/api/news?limit=100`, {
        next: { revalidate: 900 },
      });
    }
    if (response.ok) articles = await response.json();
  } catch (error) {
    console.error("News sitemap fetch error:", error);
  }

  const cutoff = Date.now() - NEWS_WINDOW_MS;
  const urls = (Array.isArray(articles) ? articles : [])
    .filter((article) => {
      const publishedAt = Date.parse(article.published_at || "");
      return Number.isFinite(publishedAt) && publishedAt >= cutoff;
    })
    .map(
      (article) => `  <url>
    <loc>${escapeXml(`${SITE_URL}/maqola/${article.slug}`)}</loc>
    <news:news>
      <news:publication>
        <news:name>${escapeXml(SITE_NAME)}</news:name>
        <news:language>uz</news:language>
      </news:publication>
      <news:publication_date>${escapeXml(new Date(article.published_at).toISOString())}</news:publication_date>
      <news:title>${escapeXml(article.title)}</news:title>
    </news:news>
  </url>`,
    )
    .join("\n");

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
${urls}
</urlset>`;

  return new Response(xml, {
    headers: {
      "Content-Type": "application/xml; charset=utf-8",
      "Cache-Control": "public, s-maxage=900, stale-while-revalidate=3600",
    },
  });
}
