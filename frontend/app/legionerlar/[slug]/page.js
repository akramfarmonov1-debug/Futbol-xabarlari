import { cache } from "react";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import ApiUnavailable from "../../../components/ApiUnavailable";
import ArticleCard from "../../../components/ArticleCard";
import { apiGetOrThrow } from "../../../lib/api";
import { truncateSeoText } from "../../../lib/seo";
import { SITE_NAME, SITE_URL } from "../../../lib/site";

const getLegionnaire = cache((slug) =>
  apiGetOrThrow(`/api/legionnaires/${encodeURIComponent(slug)}`),
);

export async function generateStaticParams() {
  return [];
}

export async function generateMetadata({ params }) {
  const { slug } = await params;
  let player = null;
  try {
    player = await getLegionnaire(slug);
  } catch {
    return { title: "Legioner haqida ma'lumot" };
  }

  if (!player) {
    return { title: "Legioner topilmadi" };
  }

  const title = truncateSeoText(
    `${player.name} (${player.club}) — yangiliklar, statistika va transfer narxi`,
    65,
  );
  const description = truncateSeoText(
    `${player.name} — O‘zbekiston terma jamoasi va «${player.club}» (${player.league}) futbolchisi. Bozor bahosi: ${player.market_value}. So‘nggi yangiliklar va natijalar — ${SITE_NAME}.`,
    160,
  );
  const canonical = `/legionerlar/${player.slug}`;

  return {
    title,
    description,
    alternates: { canonical },
    openGraph: {
      title: `${player.name} — ${SITE_NAME}`,
      description,
      url: `${SITE_URL}${canonical}`,
      siteName: SITE_NAME,
      ...(player.image_url ? { images: [{ url: player.image_url }] } : {}),
    },
  };
}

export default async function LegionnaireDetailPage({ params }) {
  const { slug } = await params;
  let player = null;

  try {
    player = await getLegionnaire(slug);
  } catch (error) {
    if (error?.status === 404) notFound();
    return (
      <div className="py-6 sm:py-10">
        <ApiUnavailable />
      </div>
    );
  }

  if (!player) notFound();

  const playerUrl = `${SITE_URL}/legionerlar/${player.slug}`;
  const articles = player.articles || [];

  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Person",
        "@id": playerUrl,
        name: player.name,
        nationality: "Uzbekistan",
        jobTitle: player.position || "Futbolchi",
        description: `${player.name} — «${player.club}» (${player.league}) klubida to‘p suruvchi o‘zbekistonlik legioner futbolchi.`,
        memberOf: {
          "@type": "SportsTeam",
          name: player.club,
        },
        url: playerUrl,
        ...(player.image_url ? { image: player.image_url } : {}),
      },
      {
        "@type": "BreadcrumbList",
        itemListElement: [
          { "@type": "ListItem", position: 1, name: "Bosh sahifa", item: SITE_URL },
          { "@type": "ListItem", position: 2, name: "Legionerlar", item: `${SITE_URL}/legionerlar` },
          { "@type": "ListItem", position: 3, name: player.name, item: playerUrl },
        ],
      },
    ],
  };

  return (
    <div className="py-6 sm:py-10 space-y-8">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-slate-400">
        <Link href="/" className="hover:text-emerald-400 transition-colors">
          Bosh sahifa
        </Link>
        <span>/</span>
        <Link href="/legionerlar" className="hover:text-emerald-400 transition-colors">
          Legionerlar
        </Link>
        <span>/</span>
        <span className="text-sky-400 font-semibold">{player.name}</span>
      </nav>

      {/* Player Profile Header Card */}
      <section className="relative overflow-hidden rounded-3xl border border-slate-900 bg-gradient-to-br from-slate-950 via-slate-900/60 to-slate-950 p-6 sm:p-8 backdrop-blur-md">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="flex items-center gap-5">
            <div className="flex h-16 w-16 sm:h-20 sm:w-20 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-500/20 to-indigo-500/20 border border-sky-500/30 text-2xl sm:text-3xl font-black text-sky-300 shadow-lg shadow-sky-500/10">
              #{player.number || "UZ"}
            </div>
            <div>
              <div className="flex items-center gap-2 text-xs font-semibold text-sky-400 uppercase tracking-widest mb-1">
                <span>{player.country_flag}</span>
                <span>{player.league}</span>
              </div>
              <h1 className="text-2xl sm:text-4xl font-black text-white tracking-tight">
                {player.name}
              </h1>
              <p className="text-sm sm:text-base text-slate-300 font-medium mt-1">
                {player.club} · <span className="text-slate-400">{player.position}</span>
              </p>
            </div>
          </div>

          {/* Quick Stats Badges */}
          <div className="flex flex-wrap sm:flex-col items-start sm:items-end gap-2.5 w-full sm:w-auto pt-4 sm:pt-0 border-t sm:border-t-0 border-slate-900">
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-2 text-left sm:text-right">
              <span className="block text-[10px] font-bold text-emerald-400 uppercase tracking-wider">
                Bozor narxi
              </span>
              <span className="text-base sm:text-lg font-black text-white">
                {player.market_value || "Noma'lum"}
              </span>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 px-4 py-2 text-left sm:text-right">
              <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                Xabarlar soni
              </span>
              <span className="text-base sm:text-lg font-black text-sky-400">
                {articles.length} ta maqola
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Related News Section */}
      <section className="space-y-5">
        <div className="flex items-center justify-between border-b border-slate-900 pb-3">
          <div className="flex items-center gap-2">
            <span className="text-lg">📰</span>
            <h2 className="text-lg sm:text-xl font-extrabold text-white tracking-tight">
              {player.name} haqida so‘nggi yangiliklar
            </h2>
          </div>
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            {articles.length} ta xabar
          </span>
        </div>

        {articles.length === 0 ? (
          <div className="rounded-2xl border border-slate-900 bg-slate-950/40 p-12 text-center text-slate-400 backdrop-blur-md">
            {player.name} haqida hozircha yangiliklar chop etilmagan.
          </div>
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {articles.map((article) => (
              <ArticleCard key={article.id} article={article} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
