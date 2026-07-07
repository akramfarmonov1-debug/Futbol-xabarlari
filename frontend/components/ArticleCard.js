import Link from "next/link";

export default function ArticleCard({ article, compact = false }) {
  const stars = "⭐".repeat(Math.max(1, Math.min(5, article.importance)));
  const date = article.published_at
    ? new Date(article.published_at).toLocaleDateString("uz-UZ")
    : "";

  if (compact) {
    return (
      <Link
        href={`/maqola/${article.slug}`}
        className="block rounded-lg border border-slate-800 p-3 hover:border-green-600"
      >
        <div className="mb-1 text-xs text-slate-400">
          {article.category?.name} · {stars}
        </div>
        <div className="text-sm font-medium leading-snug">{article.title}</div>
      </Link>
    );
  }

  return (
    <article className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60 transition hover:border-green-600">
      {article.image_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={article.image_url} alt="" className="h-44 w-full object-cover" />
      ) : (
        <div className="flex h-44 w-full items-center justify-center bg-gradient-to-br from-green-950 to-slate-900 text-5xl">
          🤖
        </div>
      )}
      <div className="p-5">
        <div className="mb-2 flex items-center justify-between text-xs text-slate-400">
          <span className="rounded-full bg-green-500/10 px-2.5 py-0.5 font-semibold text-green-400">
            {article.category?.name || "AI"}
          </span>
          <span>{stars}</span>
        </div>
        <Link href={`/maqola/${article.slug}`}>
          <h2 className="mb-2 text-lg font-semibold leading-snug hover:text-green-400">
            {article.title}
          </h2>
        </Link>
        <p className="mb-3 line-clamp-3 text-sm leading-relaxed text-slate-300">
          {article.summary}
        </p>
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>{date}</span>
          <Link href={`/maqola/${article.slug}`} className="text-green-400 hover:underline">
            To&apos;liq o&apos;qish →
          </Link>
        </div>
      </div>
    </article>
  );
}
