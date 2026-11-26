import { API_URL } from "../../lib/api";
import { SITE_NAME, SITE_URL } from "../../lib/site";

export const dynamic = "force-dynamic";
export const maxDuration = 30;

const FETCH_TIMEOUT_MS = 5_000;

const FALLBACK_CATEGORIES = [
  { slug: "transferlar", name: "Transferlar" },
  { slug: "premyer-liga", name: "Premyer-liga" },
  { slug: "la-liga", name: "La Liga" },
  { slug: "seriya-a", name: "Seriya A" },
  { slug: "bundesliga", name: "Bundesliga" },
  { slug: "chempionlar-ligasi", name: "Chempionlar ligasi" },
  { slug: "jahon-futboli", name: "Jahon futboli" },
  { slug: "uzbekiston-futboli", name: "O'zbekiston futboli" },
  { slug: "terma-jamoalar", name: "Terma jamoalar" },
];

async function fetchJsonSafe(url) {
  try {
    const res = await fetch(url, {
      next: { revalidate: 900 },
      signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
    });
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

export async function GET() {
  const [rawCategories, rawArticles] = await Promise.all([
    fetchJsonSafe(`${API_URL}/api/categories`),
    fetchJsonSafe(`${API_URL}/api/news?limit=20`),
  ]);

  const categories =
    rawCategories.length > 0 ? rawCategories : FALLBACK_CATEGORIES;

  const lines = [
    `# ${SITE_NAME}`,
    "",
    "> O'zbek tilidagi futbol yangiliklari, tahlillar, o'zbek legionerlari faoliyati va turnir jadvallari portali.",
    "",
    `Asosiy sayt: ${SITE_URL}`,
    "Til: O'zbekcha (lotin yozuvi, uz)",
    "",
    "## Asosiy bo'limlar",
    `- [Bosh sahifa](${SITE_URL}/): So'nggi va muhim futbol yangiliklari`,
    `- [Turnir jadvallari](${SITE_URL}/jadval): Top-5 Yevropa ligalari, Chempionlar ligasi va O'zbekiston Superligasi`,
    `- [Legionerlar](${SITE_URL}/legionerlar): Xorijda to'p surayotgan o'zbekistonlik futbolchilar`,
    `- [Loyiha haqida](${SITE_URL}/haqida): Tahririyat va platforma haqida ma'lumot`,
    `- [Tahririyat siyosati](${SITE_URL}/tahrir-siyosati): Faktlarni tekshirish va kontent standartlari`,
    `- [Sitemap](${SITE_URL}/sitemap.xml): Barcha maqola va bo'limlar xaritasi`,
    `- [Google News Sitemap](${SITE_URL}/news-sitemap.xml): Oxirgi 48 soatlik yangiliklar`,
    "",
    "## Kategoriyalar",
    ...categories
      .filter((cat) => cat?.slug)
      .map(
        (cat) =>
          `- [${cat.name || cat.slug}](${SITE_URL}/kategoriya/${cat.slug})`,
      ),
  ];

  const articles = rawArticles.filter((a) => a?.slug && a?.title);
  if (articles.length > 0) {
    lines.push("", "## So'nggi maqolalar");
    for (const article of articles) {
      lines.push(`- [${article.title}](${SITE_URL}/maqola/${article.slug})`);
    }
  }

  return new Response(`${lines.join("\n")}\n`, {
    status: 200,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, s-maxage=900, stale-while-revalidate=3600",
    },
  });
}
