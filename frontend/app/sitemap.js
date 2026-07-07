import { API_URL } from "../lib/api";
import { SITE_URL } from "../lib/site";

async function fetchJson(url) {
  try {
    const res = await fetch(url, { next: { revalidate: 3600 } });
    return res.ok ? await res.json() : [];
  } catch (error) {
    console.error("Sitemap fetch error:", error);
    return [];
  }
}

export default async function sitemap() {
  const [articles, categories] = await Promise.all([
    fetchJson(`${API_URL}/api/news?limit=500`),
    fetchJson(`${API_URL}/api/categories`),
  ]);

  const articleUrls = (articles || []).map((article) => ({
    url: `${SITE_URL}/maqola/${article.slug}`,
    lastModified: article.published_at ? new Date(article.published_at) : new Date(),
    changeFrequency: "weekly",
    priority: 0.7,
  }));

  const categoryUrls = (categories || []).map((cat) => ({
    url: `${SITE_URL}/kategoriya/${cat.slug}`,
    lastModified: new Date(),
    changeFrequency: "daily",
    priority: 0.8,
  }));

  const staticUrls = ["/haqida", "/aloqa", "/maxfiylik"].map((path) => ({
    url: `${SITE_URL}${path}`,
    lastModified: new Date(),
    changeFrequency: "monthly",
    priority: 0.4,
  }));

  return [
    {
      url: SITE_URL,
      lastModified: new Date(),
      changeFrequency: "always",
      priority: 1.0,
    },
    ...categoryUrls,
    ...staticUrls,
    ...articleUrls,
  ];
}
