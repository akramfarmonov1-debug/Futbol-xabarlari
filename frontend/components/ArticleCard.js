import Link from "next/link";

export default function ArticleCard({ article, compact = false }) {
  const stars = "⭐".repeat(Math.max(1, Math.min(5, article.importance)));
  const date = article.published_at
    ? new Date(article.published_at).toLocaleDateString("uz-UZ", {
        day: "numeric",
        month: "short",
      })
    : "";

  if (compact) {
    return (
      <Link
        href={`/maqola/${article.slug}`}
        className="group block rounded-xl border border-slate-900 bg-slate-950/40 p-4 hover:border-emerald-500/30 hover:bg-slate-900/40 transition-all duration-300"
      >
        <div className="mb-2 flex items-center justify-between text-xs text-slate-500">
          <span className="font-bold text-emerald-500/80 uppercase tracking-wider">{article.category?.name}</span>
          <span>{stars}</span>
        </div>
        <div className="text-sm font-semibold leading-relaxed text-slate-200 group-hover:text-emerald-400 transition-colors duration-200 line-clamp-2">
          {article.title}
        </div>
      </Link>
    );
  }

  return (
    <article className="glass-card overflow-hidden rounded-2xl flex flex-col h-full">
      {/* Article Image / Gradient placeholder */}
      <Link href={`/maqola/${article.slug}`} className="relative block overflow-hidden aspect-video w-full group">
        {article.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img 
            src={article.image_url} 
            alt={article.title} 
            className="h-full w-full object-cover group-hover:scale-105 transition-all duration-700 ease-out" 
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-emerald-950/40 to-slate-950 text-5xl">
            ⚽
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent opacity-60"></div>
      </Link>

      {/* Article Body */}
      <div className="flex flex-col flex-1 p-5 sm:p-6">
        <div className="mb-3.5 flex items-center justify-between text-xs sm:text-sm">
          <span className="rounded-full bg-emerald-500/10 px-3 py-1 font-bold text-xs uppercase tracking-wider text-emerald-400 border border-emerald-500/10">
            {article.category?.name || "AI"}
          </span>
          <span className="text-xs tracking-wide">{stars}</span>
        </div>

        <Link href={`/maqola/${article.slug}`} className="group/title">
          <h2 className="mb-3 text-lg sm:text-xl font-bold leading-snug text-white group-hover/title:text-emerald-400 transition-colors duration-200 line-clamp-2">
            {article.title}
          </h2>
        </Link>

        <p className="mb-4 line-clamp-3 text-sm leading-relaxed text-slate-400 flex-1">
          {article.summary}
        </p>

        <div className="flex items-center justify-between border-t border-slate-900/80 pt-4 text-xs sm:text-sm font-semibold">
          <span className="text-slate-500">{date}</span>
          <Link 
            href={`/maqola/${article.slug}`} 
            className="flex items-center gap-1 text-emerald-400 hover:text-emerald-300 transition-colors duration-200"
          >
            Batafsil 
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        </div>
      </div>
    </article>
  );
}
