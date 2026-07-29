import { API_URL } from "../lib/api";
import { SITE_URL } from "../lib/site";

const ARTICLE_PAGE_SIZE = 400;

async function fetchJson(url) {
  try {
    const res = await fetch(url, { next: { revalidate: 3600 } });
    return res.ok ? await res.json() : [];
  } catch (error) {
    console.error("Sitemap fetch error:", error);
    return [];
  }
}

async function fetchAllArticles() {
  const articles = [];

  for (let offset = 0; ; offset += ARTICLE_PAGE_SIZE) {
    const page = await fetchJson(
      `${API_URL}/api/news?limit=${ARTICLE_PAGE_SIZE}&offset=${offset}`,
    );

    if (!Array.isArray(page) || page.length === 0) break;
    articles.push(...page);
    if (page.length < ARTICLE_PAGE_SIZE) break;
  }

  return articles;
}

export default async function sitemap() {
  const [articles, categories] = await Promise.all([
    fetchAllArticles(),
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

  const staticUrls = [
    { path: "/jadval", changeFrequency: "hourly", priority: 0.7 },
    { path: "/haqida", changeFrequency: "monthly", priority: 0.4 },
    { path: "/aloqa", changeFrequency: "monthly", priority: 0.4 },
    { path: "/maxfiylik", changeFrequency: "monthly", priority: 0.4 },
  ].map(({ path, changeFrequency, priority }) => ({
    url: `${SITE_URL}${path}`,
    lastModified: new Date(),
    changeFrequency,
    priority,
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
