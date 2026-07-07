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
    <div className="py-8">
      <h1 className="mb-6 text-2xl font-bold">
        🔍 Qidiruv{q ? `: «${q}»` : ""}
      </h1>
      {!q ? (
        <p className="text-slate-400">Yuqoridagi qidiruv maydonidan foydalaning.</p>
      ) : (articles || []).length > 0 ? (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {articles.map((article) => (
            <ArticleCard key={article.id} article={article} />
          ))}
        </div>
      ) : (
        <p className="text-slate-400">Hech narsa topilmadi.</p>
      )}
    </div>
  );
}
