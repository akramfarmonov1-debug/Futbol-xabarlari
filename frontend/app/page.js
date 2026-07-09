import Link from "next/link";
import ArticleCard from "../components/ArticleCard";
import AdPlaceholder from "../components/AdPlaceholder";
import LiveScores from "../components/LiveScores";
import { apiGet } from "../lib/api";

export default async function HomePage() {
  const [latest, top, digest, trends] = await Promise.all([
    apiGet("/api/news", { limit: 13 }),
    apiGet("/api/news/top", { limit: 5, kunlar: 1 }),
    apiGet("/api/news/digest"),
    apiGet("/api/news/trends"),
  ]);

  const hasContent = (latest || []).length > 0;
  const heroArticle = hasContent ? latest[0] : null;
  const remainingArticles = hasContent ? latest.slice(1) : [];

  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_320px]">
      {/* Main Content Area */}
      <div className="space-y-8">
        {/* Live Scores (Mobile only, placed at the top) */}
        <div className="lg:hidden">
          <LiveScores />
        </div>

        {/* Hero Feature Article */}
        {heroArticle && (
          <section className="group relative overflow-hidden rounded-3xl border border-slate-900 bg-slate-950/40 p-5 sm:p-7 backdrop-blur-md hover:border-emerald-500/20 transition-all duration-300">
            <div className="grid gap-6 md:grid-cols-2 items-center">
              {/* Image */}
              <Link href={`/maqola/${heroArticle.slug}`} className="relative block overflow-hidden rounded-2xl aspect-video md:aspect-[4/3] w-full bg-slate-950">
                {heroArticle.image_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={heroArticle.image_url}
                    alt={heroArticle.title}
                    className="h-full w-full object-cover group-hover:scale-102 transition-transform duration-700 ease-out"
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-emerald-950/30 to-slate-950 text-6xl">
                    📰
                  </div>
                )}
                <span className="absolute left-4 top-4 rounded-full bg-emerald-500 px-3.5 py-1.5 text-xs font-extrabold uppercase tracking-widest text-slate-950 shadow-md">
                  Asosiy Mavzu
                </span>
              </Link>

              {/* Text Context */}
              <div className="flex flex-col h-full justify-center">
                <div className="mb-4 flex items-center gap-3 text-xs sm:text-sm">
                  <span className="rounded-full bg-emerald-500/10 px-3 py-1 font-bold text-xs uppercase tracking-wider text-emerald-400 border border-emerald-500/10">
                    {heroArticle.category?.name || "AI"}
                  </span>
                  <span className="text-slate-500 font-medium">
                    {"⭐".repeat(Math.max(1, Math.min(5, heroArticle.importance)))}
                  </span>
                </div>

                <Link href={`/maqola/${heroArticle.slug}`}>
                  <h1 className="mb-4 text-2xl sm:text-3xl font-extrabold leading-tight text-white hover:text-emerald-400 transition-colors duration-200">
                    {heroArticle.title}
                  </h1>
                </Link>

                <p className="mb-5 text-sm sm:text-base leading-relaxed text-slate-400 line-clamp-3">
                  {heroArticle.summary}
                </p>

                <div className="flex items-center justify-between border-t border-slate-900/60 pt-4">
                  <span className="text-xs sm:text-sm text-slate-500 font-semibold">
                    {heroArticle.published_at
                      ? new Date(heroArticle.published_at).toLocaleDateString("uz-UZ", {
                          day: "numeric",
                          month: "long",
                        })
                      : ""}
                  </span>
                  <Link
                    href={`/maqola/${heroArticle.slug}`}
                    className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500 px-6 py-2.5 text-xs sm:text-sm font-bold text-slate-950 hover:bg-emerald-400 hover:scale-[1.02] active:scale-[0.98] transition-all"
                  >
                    O&apos;qish
                    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                    </svg>
                  </Link>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Regular Articles Feed */}
        <section>
          <div className="mb-6 flex items-center justify-between border-b border-slate-900 pb-3.5">
            <h2 className="text-sm sm:text-base font-extrabold uppercase tracking-widest text-slate-200">
              ⚡ So&apos;nggi Yangiliklar
            </h2>
          </div>

          {hasContent ? (
            <div className="grid gap-6 sm:grid-cols-2">
              {remainingArticles.map((article) => (
                <ArticleCard key={article.id} article={article} />
              ))}
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-950 bg-slate-950/20 p-10 text-center leading-relaxed text-slate-500 text-sm">
              Hozircha chop etilgan yangiliklar yo&apos;q.
            </div>
          )}
        </section>
      </div>

      {/* Sidebar Area */}
      <aside className="space-y-8">
        {/* Desktop Live Scores */}
        <div className="hidden lg:block">
          <LiveScores />
        </div>

        {/* Daily Digest */}
        {(digest || []).length > 0 && (
          <section className="rounded-2xl border border-slate-900 bg-slate-950/40 p-5 backdrop-blur-md">
            <div className="mb-4 flex items-center gap-2 border-b border-slate-900 pb-2.5">
              <span className="text-base sm:text-lg">☀️</span>
              <h2 className="text-xs sm:text-sm font-extrabold uppercase tracking-wider text-slate-200">
                Bugungi Futbol Dayjesti
              </h2>
            </div>
            <ul className="space-y-3.5">
              {digest.map((article, idx) => (
                <li key={article.id} className="group flex items-start gap-3 text-sm font-medium leading-relaxed">
                  <span className="flex h-5.5 w-5.5 shrink-0 items-center justify-center rounded-md bg-emerald-500/10 text-[11px] font-bold text-emerald-400 border border-emerald-500/10">
                    {idx + 1}
                  </span>
                  <Link href={`/maqola/${article.slug}`} className="text-slate-300 hover:text-emerald-400 transition-colors">
                    {article.title}
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Top 5 Chart */}
        <section className="rounded-2xl border border-slate-900 bg-slate-950/40 p-5 backdrop-blur-md">
          <div className="mb-4 flex items-center gap-2 border-b border-slate-900 pb-2.5">
            <span className="text-base sm:text-lg">🔥</span>
            <h2 className="text-xs sm:text-sm font-extrabold uppercase tracking-wider text-slate-200">
              Top 5 Kunlik
            </h2>
          </div>
          <div className="space-y-4">
            {(top || []).length > 0 ? (
              top.map((article, index) => (
                <Link
                  key={article.id}
                  href={`/maqola/${article.slug}`}
                  className="group flex items-start gap-3.5 text-sm hover:bg-slate-900/10 p-1.5 rounded-lg transition-colors"
                >
                  <span className="text-2xl font-extrabold text-slate-800 group-hover:text-emerald-500/60 transition-colors leading-none w-7 shrink-0 text-center">
                    0{index + 1}
                  </span>
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-500/80">
                      {article.category?.name}
                    </span>
                    <h3 className="font-semibold text-slate-200 group-hover:text-emerald-400 transition-colors line-clamp-2 leading-snug">
                      {article.title}
                    </h3>
                  </div>
                </Link>
              ))
            ) : (
              <p className="text-xs sm:text-sm text-slate-500">Hali yangiliklar yo&apos;q.</p>
            )}
          </div>
        </section>

        {/* Ad Space */}
        <AdPlaceholder type="sidebar" />

        {/* Trend Tags */}
        <section className="rounded-2xl border border-slate-900 bg-slate-950/40 p-5 backdrop-blur-md">
          <div className="mb-4 flex items-center gap-2 border-b border-slate-900 pb-2.5">
            <span className="text-base sm:text-lg">📈</span>
            <h2 className="text-xs sm:text-sm font-extrabold uppercase tracking-wider text-slate-200">
              Trend Mavzular
            </h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {(trends || []).length > 0 ? (
              trends.map((trend) => (
                <Link
                  key={trend.teg}
                  href={`/qidiruv?q=${encodeURIComponent(trend.teg)}`}
                  className="rounded-full border border-slate-900 bg-slate-950/60 px-3.5 py-2 text-xs font-bold text-slate-300 hover:border-emerald-500/30 hover:bg-emerald-500 hover:text-slate-950 transition-all duration-200"
                >
                  #{trend.teg} <span className="text-slate-500 font-medium group-hover:text-inherit">({trend.soni})</span>
                </Link>
              ))
            ) : (
              <p className="text-xs sm:text-sm text-slate-500">Mavzular shakllanmagan.</p>
            )}
          </div>
        </section>
      </aside>
    </div>
  );
}
