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
    <div className="py-8">
      <h1 className="mb-6 text-2xl font-bold">📂 {category?.name || slug}</h1>
      {(articles || []).length > 0 ? (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {articles.map((article) => (
            <ArticleCard key={article.id} article={article} />
          ))}
        </div>
      ) : (
        <p className="text-slate-400">Bu kategoriyada hali yangiliklar yo&apos;q.</p>
      )}
    </div>
  );
}
