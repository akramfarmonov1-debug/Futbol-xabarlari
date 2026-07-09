import ArticleCard from "../../../components/ArticleCard";
import { apiGet } from "../../../lib/api";

export async function generateMetadata({ params }) {
  const { slug } = await params;
  const categories = (await apiGet("/api/categories")) || [];
  const category = categories.find((c) => c.slug === slug);
  const name = category?.name || slug;

  return {
    title: `${name} yangiliklari`,
    description: `${name} bo'yicha eng so'nggi jahon futboli yangiliklari — o'zbek tilida.`,
    alternates: { canonical: `/kategoriya/${slug}` },
    openGraph: {
      title: `${name} yangiliklari`,
      description: `${name} bo'yicha eng so'nggi futbol yangiliklari — o'zbek tilida.`,
      url: `/kategoriya/${slug}`,
    },
  };
}

export default async function CategoryPage({ params }) {
  const { slug } = await params;
  const [articles, categories] = await Promise.all([
    apiGet("/api/news", { kategoriya: slug, limit: 24 }),
    apiGet("/api/categories"),
  ]);
  const category = (categories || []).find((c) => c.slug === slug);

  return (
    <div className="py-4 sm:py-8 space-y-6">
      {/* Category Header */}
      <div>
        <span className="text-[10px] font-extrabold uppercase tracking-widest text-emerald-500">
          Kategoriya
        </span>
        <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2 mt-1">
          <span>📂</span> {category?.name || slug}
        </h1>
      </div>

      {/* Grid List */}
      {(articles || []).length > 0 ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {articles.map((article) => (
            <ArticleCard key={article.id} article={article} />
          ))}
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-900 bg-slate-950/20 p-10 text-center text-slate-500">
          Bu ruknda hozircha yangiliklar chop etilmagan.
        </div>
      )}
    </div>
  );
}
