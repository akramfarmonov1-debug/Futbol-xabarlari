import Link from "next/link";
import ArticleCard from "../components/ArticleCard";
import AdPlaceholder from "../components/AdPlaceholder";
import LiveScores from "../components/LiveScores";
import { apiGet } from "../lib/api";

export default async function HomePage() {
  const [latest, top, digest, trends] = await Promise.all([
    apiGet("/api/news", { limit: 12 }),
    apiGet("/api/news/top", { limit: 10, kunlar: 1 }),
    apiGet("/api/news/digest"),
    apiGet("/api/news/trends"),
  ]);

  const hasContent = (latest || []).length > 0;

  return (
    <div className="grid gap-8 py-8 lg:grid-cols-[1fr_300px]">
      <div>
        <h1 className="mb-5 text-2xl font-bold">📰 Eng so&apos;nggi futbol yangiliklari</h1>
        {hasContent ? (
          <div className="grid gap-5 sm:grid-cols-2">
            {latest.map((article) => (
              <ArticleCard key={article.id} article={article} />
            ))}
          </div>
        ) : (
          <div className="rounded-xl border border-slate-800 p-10 text-center leading-relaxed text-slate-400">
            Hozircha chop etilgan yangiliklar yo&apos;q.
            <br />
            Backend&apos;da <code className="rounded bg-slate-800 px-2 py-0.5">python -m app.pipeline</code>{" "}
            buyrug&apos;ini ishga tushiring va admin panelda tasdiqlang.
          </div>
        )}

        {(digest || []).length > 0 && (
          <section className="mt-10">
            <h2 className="mb-4 text-xl font-bold">☀️ Bugungi futbol dayjesti</h2>
            <ul className="space-y-2">
              {digest.map((article) => (
                <li key={article.id} className="flex items-start gap-2 text-sm">
                  <span>{"⭐".repeat(article.importance)}</span>
                  <Link href={`/maqola/${article.slug}`} className="hover:text-green-400">
                    {article.title}
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>

      <aside className="space-y-8">
        <LiveScores />

        <section>
          <h2 className="mb-3 font-bold">🔥 Top 10 kunlik</h2>
          <div className="space-y-2">
            {(top || []).length > 0 ? (
              top.map((article) => (
                <ArticleCard key={article.id} article={article} compact />
              ))
            ) : (
              <p className="text-sm text-slate-500">Bugun hali yangiliklar yo&apos;q.</p>
            )}
          </div>
        </section>

        <section>
          <AdPlaceholder type="sidebar" />
        </section>

        <section>
          <h2 className="mb-3 font-bold">📈 Trend mavzular</h2>
          <div className="flex flex-wrap gap-2">
            {(trends || []).length > 0 ? (
              trends.map((trend) => (
                <Link
                  key={trend.teg}
                  href={`/qidiruv?q=${encodeURIComponent(trend.teg)}`}
                  className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300 hover:bg-green-600 hover:text-white"
                >
                  #{trend.teg} <span className="text-slate-500">({trend.soni})</span>
                </Link>
              ))
            ) : (
              <p className="text-sm text-slate-500">Trendlar hali shakllanmadi.</p>
            )}
          </div>
        </section>
      </aside>
    </div>
  );
}
