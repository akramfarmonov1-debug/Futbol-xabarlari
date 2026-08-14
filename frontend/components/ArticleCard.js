import Image from "next/image";
import Link from "next/link";
import { formatUzDate } from "../lib/date";

export function formatViews(count) {
  if (!count) return "0";
  if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`;
  if (count >= 1000) return `${(count / 1000).toFixed(1)}k`;
  return String(count);
}

export default function ArticleCard({ article, compact = false }) {
  const stars = "⭐".repeat(Math.max(1, Math.min(5, article.importance)));
  const readingMinutes = Math.max(
    1,
    Math.ceil((article.content || article.summary || "").split(/\s+/).length / 200),
  );
  const date = formatUzDate(article.published_at);

  if (compact) {
    return (
      <Link
        href={`/maqola/${article.slug}`}
        className="group block rounded-xl border border-slate-900 bg-slate-950/40 p-4 hover:border-emerald-500/30 hover:bg-slate-900/40 transition-all duration-300"
      >
        <div className="mb-2 flex items-center justify-between text-xs text-slate-500">
          <span className="font-bold text-emerald-500/80 uppercase tracking-wider">
            {article.category?.name}
          </span>
          <span className="flex items-center gap-1 text-[11px] text-slate-400 font-medium">
            <span>👁</span>
            <span>{formatViews(article.views_count)}</span>
          </span>
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
          <Image
            src={article.image_url}
            alt={article.title}
            fill
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 370px"
            className="object-cover group-hover:scale-105 transition-all duration-700 ease-out"
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
          <div className="flex items-center gap-2 text-slate-500 text-xs">
            <span>{date}</span>
            <span>•</span>
            <span className="flex items-center gap-1 font-medium text-slate-400">
              <span>👁</span>
              <span>{formatViews(article.views_count)}</span>
            </span>
          </div>
          <Link 
            href={`/maqola/${article.slug}`} 
            className="flex items-center gap-1 text-emerald-400 hover:text-emerald-300 transition-colors duration-200"
          >
            O&apos;qish
            <span className="text-sm">→</span>
          </Link>
        </div>
      </div>
    </article>
  );
}
