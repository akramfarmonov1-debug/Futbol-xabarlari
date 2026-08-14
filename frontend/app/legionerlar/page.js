import Link from "next/link";
import ArticleCard from "../../components/ArticleCard";
import { apiGet } from "../../lib/api";
import { SITE_NAME, SITE_URL } from "../../lib/site";

export const metadata = {
  title: "O‘zbekistonlik Legionerlar — Xorijiy Ligalardagi Futbolchilarimiz",
  description:
    "Abduqodir Husanov, Abbosbek Fayzullayev, Eldor Shomurodov va boshqa o‘zbek legionerlarining klublari, transfer qiymati va so‘nggi yangiliklari.",
  alternates: { canonical: "/legionerlar" },
  openGraph: {
    title: "O‘zbekistonlik Legionerlar — Futbol Xabar",
    description:
      "Xorijiy chempionatlarda to‘p surayotgan o‘zbekistonlik futbolchilar haqida eng so‘nggi yangiliklar va ma'lumotlar.",
    url: `${SITE_URL}/legionerlar`,
    siteName: SITE_NAME,
  },
};

export default async function LegionnairesPage() {
  const legionnaires = (await apiGet("/api/legionnaires")) || [];

  return (
    <div className="py-6 sm:py-10">
      {/* Header */}
      <div className="mb-8 rounded-2xl border border-slate-900 bg-gradient-to-br from-slate-950 via-slate-900/50 to-slate-950 p-6 sm:p-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-sky-500/10 px-3.5 py-1 text-xs font-bold text-sky-400 border border-sky-500/20 mb-3">
              🇺🇿 Milliy Faxrlarimiz
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              O‘zbekistonlik Legionerlar
            </h1>
            <p className="mt-2 max-w-2xl text-xs sm:text-sm text-slate-400 leading-relaxed">
              Yevropa va Osiyoning yetakchi ligalarida to‘p surayotgan o‘zbekistonlik
              futbolchilar profili, bozor bahosi va ularga oid so‘nggi yangiliklar.
            </p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 text-center">
            <span className="block text-2xl font-black text-sky-400">
              {legionnaires.length}
            </span>
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Asosiy Legionerlar
            </span>
          </div>
        </div>
      </div>

      {/* Legionnaires Grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {legionnaires.map((player) => (
          <div
            key={player.id}
            className="flex flex-col justify-between rounded-2xl border border-slate-900 bg-slate-950/60 p-5 hover:border-slate-800 transition-all duration-200"
          >
            <div>
              {/* Player Top Bar */}
              <div className="flex items-start justify-between gap-3 mb-4">
                <div className="flex items-center gap-3.5">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-500/20 via-indigo-500/20 to-emerald-500/20 border border-sky-500/30 text-sm font-black text-sky-300 shadow-md shadow-sky-500/5">
                    #{player.number}
                  </div>
                  <div>
                    <h2 className="text-base font-extrabold text-white">
                      {player.name}
                    </h2>
                    <p className="text-xs font-semibold text-slate-300 flex items-center gap-1.5 mt-0.5">
                      <span>{player.country_flag}</span>
                      <span>{player.club}</span>
                    </p>
                  </div>
                </div>

                <div className="text-right">
                  <span className="inline-block rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-black text-emerald-400 border border-emerald-500/20">
                    {player.market_value}
                  </span>
                  <span className="block text-[10px] text-slate-500 font-medium mt-1">
                    Bozor bahosi
                  </span>
                </div>
              </div>

              {/* Specs */}
              <div className="grid grid-cols-2 gap-2 rounded-xl bg-slate-900/40 p-3 text-xs text-slate-400 mb-4 border border-slate-900">
                <div>
                  <span className="block text-[10px] uppercase font-bold text-slate-500">
                    Pozitsiya
                  </span>
                  <span className="font-semibold text-slate-200">
                    {player.position}
                  </span>
                </div>
                <div>
                  <span className="block text-[10px] uppercase font-bold text-slate-500">
                    Chempionat
                  </span>
                  <span className="font-semibold text-slate-200 truncate block">
                    {player.league}
                  </span>
                </div>
              </div>

              {/* Recent news */}
              {player.recent_articles && player.recent_articles.length > 0 && (
                <div className="mb-4">
                  <span className="block text-[11px] font-bold text-slate-400 mb-2 uppercase tracking-wider">
                    So‘nggi xabarlar:
                  </span>
                  <div className="space-y-1.5">
                    {player.recent_articles.map((art) => (
                      <Link
                        key={art.id}
                        href={`/maqola/${art.slug}`}
                        className="group/item flex items-center justify-between rounded-lg bg-slate-900/20 px-3 py-2 text-xs font-medium text-slate-300 hover:bg-slate-900/60 hover:text-sky-400 transition-colors"
                      >
                        <span className="truncate pr-2">{art.title}</span>
                        <span className="shrink-0 text-slate-600 group-hover/item:text-sky-400">
                          →
                        </span>
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Action */}
            <div className="border-t border-slate-900 pt-3">
              <Link
                href={`/qidiruv?q=${encodeURIComponent(player.name)}`}
                className="flex items-center justify-center gap-1.5 rounded-xl border border-slate-800 bg-slate-900/40 py-2.5 text-xs font-bold text-slate-300 hover:border-sky-500/30 hover:bg-sky-500 hover:text-slate-950 transition-all duration-200"
              >
                <span>🔍</span>
                <span>{player.name} haqidagi barcha xabarlar</span>
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
