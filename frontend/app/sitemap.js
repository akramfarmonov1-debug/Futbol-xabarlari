import { API_URL } from "../lib/api";
import { SITE_URL } from "../lib/site";

// Sitemap ma'lumotlari build vaqtida tashqi backendga bog'lanib qolmasin.
// Route so'rov paytida generatsiya qilinadi va backend vaqtincha uxlab qolsa
// qisqa muddat ichida bo'sh sitemap bilan xavfsiz davom etadi.
export const dynamic = "force-dynamic";
export const revalidate = 3600;

const FETCH_ATTEMPTS = 2;
const FETCH_TIMEOUT_MS = 5_000;
const LEGACY_PAGE_SIZE = 400;

async function fetchJson(url) {
  for (let attempt = 1; attempt <= FETCH_ATTEMPTS; attempt += 1) {
    try {
      const res = await fetch(url, {
        next: { revalidate: 3600 },
        signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
      });
      if (res.ok) return await res.json();
      console.error(`Sitemap fetch error: HTTP ${res.status} (${url})`);
    } catch (error) {
      console.error(`Sitemap fetch attempt ${attempt} failed:`, error);
    }

    if (attempt < FETCH_ATTEMPTS) {
      await new Promise((resolve) => setTimeout(resolve, attempt * 250));
    }
  }

  return [];
}

async function fetchLegacyArticles() {
  const articles = [];

  for (let offset = 0; ; offset += LEGACY_PAGE_SIZE) {
    const page = await fetchJson(
      `${API_URL}/api/news?limit=${LEGACY_PAGE_SIZE}&offset=${offset}&_sitemap=v2`,
    );
    if (!Array.isArray(page) || page.length === 0) break;
    articles.push(
      ...page.map((article) => ({
        slug: article.slug,
        title: article.title,
        published_at: article.published_at,
        category_slug: article.category?.slug || null,
      })),
    );
    if (page.length < LEGACY_PAGE_SIZE) break;
  }

  return articles;
}

export default async function sitemap() {
  const [sitemapArticles, categories] = await Promise.all([
    fetchJson(`${API_URL}/api/news/sitemap`),
    fetchJson(`${API_URL}/api/categories`),
  ]);
  const articles =
    Array.isArray(sitemapArticles) && sitemapArticles.length > 0
      ? sitemapArticles
      : await fetchLegacyArticles();

  const articleUrls = (articles || []).map((article) => ({
    url: `${SITE_URL}/maqola/${article.slug}`,
    lastModified: article.published_at ? new Date(article.published_at) : new Date(),
    changeFrequency: "weekly",
    priority: 0.7,
  }));

  const categoryUrls = (categories || []).map((cat) => {
    const latestArticle = articles.find(
      (article) => article.category_slug === cat.slug && article.published_at,
    );

    return {
      url: `${SITE_URL}/kategoriya/${cat.slug}`,
      ...(latestArticle
        ? { lastModified: new Date(latestArticle.published_at) }
        : {}),
      changeFrequency: "daily",
      priority: 0.8,
    };
  });

  const staticUrls = [
    { path: "/jadval", changeFrequency: "hourly", priority: 0.7 },
    { path: "/haqida", changeFrequency: "monthly", priority: 0.4 },
    { path: "/aloqa", changeFrequency: "monthly", priority: 0.4 },
    { path: "/maxfiylik", changeFrequency: "monthly", priority: 0.4 },
  ].map(({ path, changeFrequency, priority }) => ({
    url: `${SITE_URL}${path}`,
    changeFrequency,
    priority,
  }));

  const latestPublishedAt = articles.find((article) => article.published_at)
    ?.published_at;

  return [
    {
      url: SITE_URL,
      ...(latestPublishedAt
        ? { lastModified: new Date(latestPublishedAt) }
        : {}),
      changeFrequency: "always",
      priority: 1.0,
    },
    ...categoryUrls,
    ...staticUrls,
    ...articleUrls,
  ];
}
