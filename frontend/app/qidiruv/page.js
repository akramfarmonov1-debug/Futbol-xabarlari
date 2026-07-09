import ArticleCard from "../../components/ArticleCard";
import { apiGet } from "../../lib/api";

export const metadata = {
  title: "Qidiruv",
  robots: { index: false, follow: true },
};

export default async function SearchPage({ searchParams }) {
  const { q } = await searchParams;
  const articles = q ? await apiGet("/api/news/search", { q }) : [];

  return (
    <div className="py-4 sm:py-8 space-y-6">
      {/* Header */}
      <div>
        <span className="text-[10px] font-extrabold uppercase tracking-widest text-emerald-500">
          Qidiruv Natijalari
        </span>
        <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2 mt-1">
          <span>🔍</span> {q ? `«${q}» bo'yicha` : "Qidiruv"}
        </h1>
      </div>

      {/* Grid Results */}
      {!q ? (
        <div className="rounded-2xl border border-slate-900 bg-slate-950/20 p-10 text-center text-slate-500">
          Yuqoridagi qidiruv maydonidan foydalanib kalit so&apos;zni kiriting.
        </div>
      ) : (articles || []).length > 0 ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {articles.map((article) => (
            <ArticleCard key={article.id} article={article} />
          ))}
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-900 bg-slate-950/20 p-10 text-center text-slate-500">
          Ushbu so&apos;rov bo&apos;yicha hech qanday yangilik topilmadi.
        </div>
      )}
    </div>
  );
}
