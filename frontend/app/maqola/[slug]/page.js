import Link from "next/link";
import AdPlaceholder from "../../../components/AdPlaceholder";
import { apiGet } from "../../../lib/api";
import { SITE_URL, SITE_NAME } from "../../../lib/site";

export async function generateMetadata({ params }) {
  const { slug } = await params;
  const article = await apiGet(`/api/news/${slug}`);
  if (!article) return { title: "Maqola topilmadi" };

  const title = article.seo_title || article.title;
  const url = `/maqola/${article.slug}`;

  return {
    title,
    description: article.summary,
    keywords: article.tags || [],
    alternates: { canonical: url },
    openGraph: {
      type: "article",
      url,
      siteName: SITE_NAME,
      locale: "uz_UZ",
      title,
      description: article.summary,
      publishedTime: article.published_at || article.created_at,
      section: article.category?.name,
      tags: article.tags || [],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description: article.summary,
    },
  };
}

function articleJsonLd(article) {
  const url = `${SITE_URL}/maqola/${article.slug}`;
  return {
    "@context": "https://schema.org",
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
  };
}

export default async function ArticlePage({ params }) {
  const { slug } = await params;
  const article = await apiGet(`/api/news/${slug}`);

  if (!article) {
    return (
      <div className="py-20 text-center text-slate-400">
        Maqola topilmadi. <Link href="/" className="text-green-400">Bosh sahifaga qaytish</Link>
      </div>
    );
  }

  const stars = "⭐".repeat(Math.max(1, Math.min(5, article.importance)));
  const date = article.published_at
    ? new Date(article.published_at).toLocaleString("uz-UZ")
    : "";
  const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(`${SITE_URL}/maqola/${article.slug}`)}&text=${encodeURIComponent(article.title)}`;

  return (
    <article className="mx-auto max-w-3xl py-8">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(articleJsonLd(article)),
        }}
      />
      <div className="mb-3 flex flex-wrap items-center gap-3 text-sm text-slate-400">
        {article.category && (
          <Link
            href={`/kategoriya/${article.category.slug}`}
            className="rounded-full bg-green-500/10 px-3 py-1 font-semibold text-green-400"
          >
            {article.category.name}
          </Link>
        )}
        <span>{stars}</span>
        <span>{date}</span>
      </div>

      <h1 className="mb-4 text-3xl font-bold leading-tight">{article.title}</h1>

      {article.image_url && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={article.image_url} alt="" className="mb-6 w-full rounded-xl object-cover" />
      )}

      <p className="mb-6 border-l-4 border-green-500 pl-4 text-lg leading-relaxed text-slate-200">
        {article.summary}
      </p>

      <div className="prose-invert mb-6 space-y-4 leading-relaxed text-slate-300">
        {article.content.split(/\n\s*\n/).map((paragraph, i) => (
          <p key={i}>{paragraph}</p>
        ))}
      </div>

      {article.practical_note && (
        <div className="mb-6 rounded-xl border border-green-900 bg-green-500/5 p-5">
          <div className="mb-1 text-sm font-bold text-green-400">💡 BU NIMA DEGANI?</div>
          <p className="text-slate-200">{article.practical_note}</p>
        </div>
      )}

      <div className="mb-6 flex flex-wrap gap-2">
        {(article.tags || []).map((tag) => (
          <Link
            key={tag}
            href={`/qidiruv?q=${encodeURIComponent(tag)}`}
            className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300 hover:bg-green-600 hover:text-white"
          >
            #{tag}
          </Link>
        ))}
      </div>

      <div className="mb-8">
        <AdPlaceholder type="banner" />
      </div>

      <div className="flex flex-wrap items-center gap-4 border-t border-slate-800 pt-5 text-sm">
        <a
          href={article.original_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-green-400 hover:underline"
        >
          🔗 Asl manba ({article.source_name})
        </a>
        <a
          href={shareUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-lg bg-sky-600 px-3 py-1.5 text-white hover:bg-sky-500"
        >
          📤 Telegramda ulashish
        </a>
      </div>
    </article>
  );
}
