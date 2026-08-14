import Link from "next/link";
import { apiGet } from "../lib/api";

export default async function LegionnairesWidget() {
  const legionnaires = (await apiGet("/api/legionnaires")) || [];
  if (!legionnaires.length) return null;

  return (
    <section className="mb-10 rounded-2xl border border-slate-900 bg-gradient-to-br from-slate-950 via-slate-900/40 to-slate-950 p-5 backdrop-blur-sm">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-sky-500/10 text-sky-400 font-bold text-sm border border-sky-500/20">
            🇺🇿
          </span>
          <div>
            <h2 className="text-sm font-extrabold uppercase tracking-widest text-slate-100">
              Legionerlarimiz
            </h2>
            <p className="text-[11px] text-slate-400 font-medium">
              Xorijiy ligalardagi o‘zbek futbolchilarining so‘nggi holati
            </p>
          </div>
        </div>

        <Link
          href="/legionerlar"
          className="text-xs font-bold text-sky-400 hover:text-sky-300 transition-colors"
        >
          Barchasi →
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {legionnaires.slice(0, 6).map((player) => (
          <Link
            key={player.id}
            href={`/qidiruv?q=${encodeURIComponent(player.name)}`}
            className="group flex items-center justify-between rounded-xl border border-slate-800/80 bg-slate-900/30 p-3.5 hover:border-sky-500/40 hover:bg-slate-900/60 transition-all duration-200"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-sky-500/20 to-indigo-500/20 border border-sky-500/30 text-xs font-black text-sky-300 group-hover:scale-105 transition-transform duration-200">
                #{player.number}
              </div>
              <div className="min-w-0">
                <h3 className="truncate text-xs font-bold text-slate-100 group-hover:text-sky-400 transition-colors">
                  {player.name}
                </h3>
                <p className="truncate text-[11px] text-slate-400 font-medium">
                  {player.country_flag} {player.club}
                </p>
                <span className="text-[10px] text-slate-500">
                  {player.position}
                </span>
              </div>
            </div>

            <div className="text-right shrink-0 ml-2">
              <span className="block text-[11px] font-bold text-slate-300">
                {player.market_value}
              </span>
              {player.articles_count > 0 ? (
                <span className="inline-block rounded-full bg-emerald-500/10 px-2 py-0.5 text-[9px] font-bold text-emerald-400 border border-emerald-500/20">
                  {player.articles_count} xabar
                </span>
              ) : (
                <span className="text-[10px] text-slate-600">
                  {player.league.split(" ")[0]}
                </span>
              )}
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
