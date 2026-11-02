import { cache } from "react";
import Link from "next/link";
import ApiUnavailable from "../../../components/ApiUnavailable";
import ArticleCard from "../../../components/ArticleCard";
import { apiGetPrimary } from "../../../lib/api";
import { truncateSeoText } from "../../../lib/seo";
import { SITE_NAME, SITE_URL } from "../../../lib/site";

const getTopic = cache((slug) => apiGetPrimary(`/api/news/topic/${encodeURIComponent(slug)}`));

export async function generateStaticParams() {
  return [];
}

function humanizeSlug(slug = "") {
  return decodeURIComponent(slug)
    .replace(/-/g, " ")
    .replace(/\b\w/g, (ch) => ch.toUpperCase());
}

export async function generateMetadata({ params }) {
  const { slug } = await params;
  const data = await getTopic(slug);
  const titleName = data?.title || humanizeSlug(slug);
  const canonicalSlug = data?.slug || slug;
  const hasArticles = Array.isArray(data?.articles) && data.articles.length > 0;

  const seoTitle = truncateSeoText(
    `${titleName} yangiliklari — so‘nggi xabarlar va natijalar`,
    65,
  );
  const description = truncateSeoText(
    `${titleName} haqida eng so‘nggi futbol yangiliklari, o‘yin natijalari, transfer xabarlari va tahlillar o‘zbek tilida — ${SITE_NAME}.`,
    160,
  );

  return {
    title: seoTitle,
    description,
    alternates: { canonical: `/mavzu/${canonicalSlug}` },
    robots: hasArticles
      ? { index: true, follow: true }
      : { index: false, follow: true },
    openGraph: {
      title: `${seoTitle} — ${SITE_NAME}`,
      description,
      url: `${SITE_URL}/mavzu/${canonicalSlug}`,
      siteName: SITE_NAME,
    },
  };
}

export default async function TopicPage({ params }) {
  const { slug } = await params;
  const data = await getTopic(slug);

  if (data === null) {
    return (
      <div className="py-4 sm:py-8">
        <ApiUnavailable />
      </div>
    );
  }

  const titleName = data?.title || humanizeSlug(slug);
  const canonicalSlug = data?.slug || slug;
  const articles = data?.articles || [];
  const topicUrl = `${SITE_URL}/mavzu/${canonicalSlug}`;

  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "CollectionPage",
        "@id": topicUrl,
        url: topicUrl,
        name: `${titleName} yangiliklari`,
        description: `${titleName} bo‘yicha eng so‘nggi futbol yangiliklari va tahlillar o‘zbek tilida.`,
        inLanguage: "uz",
        isPartOf: { "@id": `${SITE_URL}/#website` },
      },
      {
        "@type": "BreadcrumbList",
        itemListElement: [
          { "@type": "ListItem", position: 1, name: "Bosh sahifa", item: SITE_URL },
          { "@type": "ListItem", position: 2, name: titleName, item: topicUrl },
        ],
      },
    ],
  };

  return (
    <div className="py-4 sm:py-8 space-y-6">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/* Breadcrumb & Header */}
      <div className="border-b border-slate-900 pb-4">
        <nav aria-label="Breadcrumb" className="mb-2 flex items-center gap-2 text-xs text-slate-400">
          <Link href="/" className="hover:text-emerald-400 transition-colors">
            Bosh sahifa
          </Link>
          <span>/</span>
          <span className="text-emerald-400 font-semibold">Mavzu</span>
        </nav>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          #{titleName} — so‘nggi yangiliklar
        </h1>
        <p className="mt-1.5 text-xs sm:text-sm text-slate-400">
          «{titleName}» mavzusiga oid barcha futbol xabarlari, natijalar va tahlillar ({articles.length} ta maqola).
        </p>
      </div>

      {/* Articles Grid */}
      {articles.length === 0 ? (
        <div className="rounded-2xl border border-slate-900 bg-slate-950/40 p-12 text-center text-slate-400 backdrop-blur-md">
          Ushbu mavzuda hozircha yangiliklar topilmadi.
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {articles.map((article) => (
            <ArticleCard key={article.id} article={article} />
          ))}
        </div>
      )}
    </div>
  );
}
