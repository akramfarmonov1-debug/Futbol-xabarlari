import ApiUnavailable from "../../../components/ApiUnavailable";
import ArticleCard from "../../../components/ArticleCard";
import { apiGet, apiGetPrimary } from "../../../lib/api";

// Bo'sh ro'yxat: kategoriyalar build'da emas, birinchi tashrifda yasaladi va
// keyin keshlanadi (ISR). Usiz dinamik sahifa har tashrifda qayta yasalardi.
export async function generateStaticParams() {
  return [];
}

export async function generateMetadata({ params, searchParams }) {
  const { slug } = await params;
  const sp = searchParams ? await searchParams : {};
  const pageNum = Math.max(1, parseInt(sp?.sahifa || "1", 10) || 1);
  const categories = (await apiGet("/api/categories")) || [];
  const category = categories.find((c) => c.slug === slug);
  const name = category?.name || slug;

  const titleSuffix = pageNum > 1 ? ` (${pageNum}-sahifa)` : "";
  const canonical = pageNum > 1 ? `/kategoriya/${slug}?sahifa=${pageNum}` : `/kategoriya/${slug}`;

  return {
    title: `${name} yangiliklari${titleSuffix}`,
    description: `${name} bo'yicha eng so'nggi jahon futboli yangiliklari — o'zbek tilida.${titleSuffix}`,
    alternates: { canonical },
    openGraph: {
      title: `${name} yangiliklari${titleSuffix}`,
      description: `${name} bo'yicha eng so'nggi futbol yangiliklari — o'zbek tilida.`,
      url: canonical,
    },
  };
}

const PAGE_SIZE = 24;

export default async function CategoryPage({ params, searchParams }) {
  const { slug } = await params;
  const sp = searchParams ? await searchParams : {};
  const currentPage = Math.max(1, parseInt(sp?.sahifa || "1", 10) || 1);
  const offset = (currentPage - 1) * PAGE_SIZE;

  const [articles, categories] = await Promise.all([
    apiGetPrimary("/api/news", {
      kategoriya: slug,
      limit: PAGE_SIZE + 1,
      offset,
    }),
    apiGet("/api/categories"),
  ]);
  const category = (categories || []).find((c) => c.slug === slug);

  const hasMore = Array.isArray(articles) && articles.length > PAGE_SIZE;
  const displayedArticles = Array.isArray(articles)
    ? articles.slice(0, PAGE_SIZE)
    : [];

  return (
    <div className="py-4 sm:py-8 space-y-6">
      {/* Category Header */}
      <div>
        <span className="text-[10px] font-extrabold uppercase tracking-widest text-emerald-500">
          Kategoriya
        </span>
        <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2 mt-1">
          <span>📂</span> {category?.name || slug}
          {currentPage > 1 && (
            <span className="text-sm font-semibold text-slate-500">
              ({currentPage}-sahifa)
            </span>
          )}
        </h1>
      </div>

      {/* Grid List */}
      {articles === null ? (
        <ApiUnavailable />
      ) : displayedArticles.length > 0 ? (
        <>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {displayedArticles.map((article) => (
              <ArticleCard key={article.id} article={article} />
            ))}
          </div>

          {/* Pagination Controls */}
          {(currentPage > 1 || hasMore) && (
            <nav
              aria-label="Sahifalar"
              className="flex items-center justify-between border-t border-slate-900 pt-6"
            >
              <div>
                {currentPage > 1 ? (
                  <a
                    href={
                      currentPage === 2
                        ? `/kategoriya/${slug}`
                        : `/kategoriya/${slug}?sahifa=${currentPage - 1}`
                    }
                    className="inline-flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-900/40 px-4 py-2 text-xs font-bold text-slate-300 hover:border-emerald-500/40 hover:text-emerald-400 transition-colors"
                  >
                    ← Oldingi sahifa
                  </a>
                ) : (
                  <span className="text-xs text-slate-600">Boshlanishi</span>
                )}
              </div>

              <span className="text-xs font-bold text-slate-400">
                {currentPage}-sahifa
              </span>

              <div>
                {hasMore ? (
                  <a
                    href={`/kategoriya/${slug}?sahifa=${currentPage + 1}`}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-2 text-xs font-bold text-emerald-400 hover:bg-emerald-500 hover:text-slate-950 transition-all duration-200"
                  >
                    Keyingi sahifa →
                  </a>
                ) : (
                  <span className="text-xs text-slate-600">Oxirgi sahifa</span>
                )}
              </div>
            </nav>
          )}
        </>
      ) : (
        <div className="rounded-2xl border border-slate-900 bg-slate-950/20 p-10 text-center text-slate-500">
          Bu ruknda hozircha yangiliklar chop etilmagan.
        </div>
      )}
    </div>
  );
}
