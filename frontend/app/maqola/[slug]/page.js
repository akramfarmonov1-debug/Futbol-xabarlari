import { cache } from "react";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import AdPlaceholder from "../../../components/AdPlaceholder";
import { apiGet } from "../../../lib/api";
import { formatUzDate, formatUzDateTime } from "../../../lib/date";
import { truncateSeoText } from "../../../lib/seo";
import { SITE_URL, SITE_NAME } from "../../../lib/site";

const getArticle = cache((slug) => apiGet(`/api/news/${slug}`));

export async function generateMetadata({ params }) {
  const { slug } = await params;
  const article = await getArticle(slug);
  if (!article) {
    return {
      title: "Maqola topilmadi",
      robots: { index: false, follow: false },
    };
  }

  const rawTitle = article.seo_title || article.title;
  const title = truncateSeoText(rawTitle, 48);
  const socialTitle = truncateSeoText(rawTitle, 90);
  const description = truncateSeoText(article.summary, 155);
  const url = `/maqola/${article.slug}`;
  const image =
    article.image_url || `${SITE_URL}/maqola/${article.slug}/opengraph-image`;

  return {
    title,
    description,
    keywords: article.tags || [],
    alternates: { canonical: url },
    openGraph: {
      type: "article",
      url,
      siteName: SITE_NAME,
      locale: "uz_UZ",
      title: socialTitle,
      description,
      publishedTime: article.published_at || article.created_at,
      section: article.category?.name,
      tags: article.tags || [],
      images: [{ url: image, alt: article.title }],
    },
    twitter: {
      card: "summary_large_image",
      title: socialTitle,
      description,
      images: [image],
    },
  };
}

function structuredData(article) {
  const url = `${SITE_URL}/maqola/${article.slug}`;
  return {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "NewsArticle",
        mainEntityOfPage: { "@type": "WebPage", "@id": url },
        headline: article.title,
        description: article.summary,
        image: [
          article.image_url?.startsWith("http")
            ? article.image_url
            : `${url}/opengraph-image`,
        ],
        datePublished: article.published_at || article.created_at,
        dateModified: article.published_at || article.created_at,
        inLanguage: "uz",
        articleSection: article.category?.name,
        keywords: (article.tags || []).join(", "),
        author: {
          "@type": "Organization",
          name: SITE_NAME,
          url: SITE_URL,
        },
        publisher: { "@id": `${SITE_URL}/#organization` },
        isBasedOn: article.original_url,
      },
      {
        "@type": "BreadcrumbList",
        itemListElement: [
          {
            "@type": "ListItem",
            position: 1,
            name: "Bosh sahifa",
            item: SITE_URL,
          },
          ...(article.category
            ? [
                {
                  "@type": "ListItem",
                  position: 2,
                  name: article.category.name,
                  item: `${SITE_URL}/kategoriya/${article.category.slug}`,
                },
              ]
            : []),
          {
            "@type": "ListItem",
            position: article.category ? 3 : 2,
            name: article.title,
            item: url,
          },
        ],
      },
    ],
  };
}

export default async function ArticlePage({ params }) {
  const { slug } = await params;
  const article = await getArticle(slug);

  if (!article) notFound();

  const stars = "⭐".repeat(Math.max(1, Math.min(5, article.importance)));
  const readingMinutes = Math.max(
    1,
    Math.ceil((article.content || "").split(/\s+/).length / 200),
  );
  const date = formatUzDateTime(article.published_at);
  const sourceDate = article.source_published_at
    ? formatUzDate(article.source_published_at, { year: true })
    : null;
  const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(`${SITE_URL}/maqola/${article.slug}`)}&text=${encodeURIComponent(article.title)}`;

  return (
    <article className="mx-auto max-w-2xl py-4 sm:py-8">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(structuredData(article)),
        }}
      />
      
      {/* Category & Date Metadata */}
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3 text-xs sm:text-sm">
        <div className="flex items-center gap-2.5">
          {article.category && (
            <Link
              href={`/kategoriya/${article.category.slug}`}
              className="rounded-full bg-emerald-500/10 px-3 py-1 font-bold text-xs uppercase tracking-wider text-emerald-400 border border-emerald-500/10"
            >
              {article.category.name}
            </Link>
          )}
          <span className="text-xs font-medium tracking-wide">{stars}</span>
        </div>
        <span className="text-slate-500 font-semibold">{date}</span>
      </div>

      {/* Main Title */}
      <h1 className="mb-6 text-3xl sm:text-4xl font-extrabold leading-tight text-white tracking-tight">
        {article.title}
      </h1>

      {/* Article Cover Image */}
      {article.image_url && (
        <div className="relative mb-6 overflow-hidden rounded-2xl border border-slate-900 aspect-video w-full bg-slate-950">
          <Image
            src={article.image_url}
            alt={article.title}
            fill
            priority
            sizes="(max-width: 768px) 100vw, 672px"
            className="object-cover"
          />
        </div>
      )}

      <div className="mb-6 grid gap-2 rounded-2xl border border-slate-900 bg-slate-950/50 p-4 text-xs text-slate-400 sm:grid-cols-3">
        <div>
          <span className="block font-bold text-slate-200">Manba</span>
          {article.source_name || "Ochiq manba"}
        </div>
        <div>
          <span className="block font-bold text-slate-200">O‘qish vaqti</span>
          Taxminan {readingMinutes} daqiqa
        </div>
        <div>
          <span className="block font-bold text-slate-200">Tayyorlash usuli</span>
          AI yordamida o‘zbekchalashtirilgan
        </div>
        {sourceDate && (
          <p className="sm:col-span-3 border-t border-slate-900 pt-2 text-[11px] text-slate-500">
            Asl xabar e’lon qilingan sana: {sourceDate}
          </p>
        )}
      </div>

      {/* Summary Highlight (Blockquote) */}
      <div className="mb-7 border-l-4 border-emerald-500 bg-emerald-950/10 p-5 rounded-r-2xl text-[15px] sm:text-lg font-semibold leading-relaxed text-slate-200">
        {article.summary}
      </div>

      {/* Body Content Paragraphs */}
      <div className="mb-8 space-y-6 text-base sm:text-[17px] leading-relaxed text-slate-300">
        {article.content.split(/\n\s*\n/).map((paragraph, i) => (
          <p key={i}>{paragraph}</p>
        ))}
      </div>

      {/* AI Explainer Box ("Bu nima degani?") */}
      {article.practical_note && (
        <div className="mb-8 rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-950/20 to-slate-950/40 p-5 backdrop-blur-sm">
          <div className="mb-2.5 flex items-center gap-2.5 text-xs sm:text-sm font-extrabold uppercase tracking-widest text-emerald-400">
            <span>💡</span>
            <span>Bu Nima Degani?</span>
          </div>
          <p className="text-sm sm:text-base leading-relaxed text-slate-300 font-medium">
            {article.practical_note}
          </p>
        </div>
      )}

      {/* Tags List */}
      <div className="mb-8 flex flex-wrap gap-2">
        {(article.tags || []).map((tag) => (
          <Link
            key={tag}
            href={`/qidiruv?q=${encodeURIComponent(tag)}`}
            className="rounded-full border border-slate-900 bg-slate-950/60 px-3.5 py-2 text-xs font-bold text-slate-300 hover:border-emerald-500/30 hover:bg-emerald-500 hover:text-slate-950 transition-all duration-200"
          >
            #{tag}
          </Link>
        ))}
      </div>

      {/* Advert Place */}
      <div className="mb-8">
        <AdPlaceholder type="banner" />
      </div>

      {/* Actions and Footer (Share/Source) */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-t border-slate-900 pt-6">
        <a
          href={article.original_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-bold text-slate-400 hover:text-emerald-400 transition-colors"
        >
          <span>🔗</span>
          <span>Asl manba ({article.source_name})</span>
        </a>
        
        <a
          href={shareUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center justify-center gap-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 px-6 py-3 text-xs sm:text-sm font-bold text-white transition-all duration-200 shadow-md shadow-sky-500/10 active:scale-[0.98]"
        >
          <svg className="h-4.5 w-4.5 fill-white" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.07-.2-.08-.06-.19-.04-.27-.02-.12.02-1.96 1.24-5.54 3.65-.52.36-.99.53-1.4.52-.46-.01-1.34-.26-1.99-.47-.8-.26-1.43-.4-1.38-.85.03-.23.35-.47.96-.71 3.76-1.64 6.27-2.72 7.53-3.25 3.58-1.51 4.32-1.77 4.81-1.78.11 0 .35.03.5.16.13.12.17.29.18.41-.01.08-.01.22-.02.26z"/>
          </svg>
          Telegramda ulashish
        </a>
      </div>
    </article>
  );
}
