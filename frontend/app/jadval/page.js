import Link from "next/link";
import { apiGet } from "../../lib/api";

export const metadata = {
  title: "Turnir jadvallari",
  description:
    "Angliya Premyer-ligasi, La Liga, Seriya A, Bundesliga va Chempionlar ligasi turnir jadvallari — jonli yangilanadi.",
  alternates: { canonical: "/jadval" },
};

export const revalidate = 3600;

// Function to get position class indicator (Champions League, Europa League, Relegation)
function getPositionIndicator(pos, total) {
  if (pos <= 4) return "border-l-[3px] border-l-emerald-500 pl-2"; // Champions League
  if (pos === 5) return "border-l-[3px] border-l-sky-500 pl-2"; // Europa League
  if (pos >= total - 2) return "border-l-[3px] border-l-red-500 pl-2"; // Relegation
  return "pl-3";
}

function getPositionBg(pos, total) {
  if (pos <= 4) return "text-emerald-400 font-bold";
  if (pos === 5) return "text-sky-400 font-bold";
  if (pos >= total - 2) return "text-red-400 font-bold";
  return "text-slate-400";
}

export default async function StandingsPage({ searchParams }) {
  const competitions = (await apiGet("/api/scores/competitions")) || [];

  if (competitions.length === 0) {
    return (
      <div className="py-24 text-center text-slate-400">
        <h1 className="mb-3 text-2xl font-extrabold text-white">🏆 Turnir Jadvallari</h1>
        <p className="text-xs">Jadval ma&apos;lumotlari hozircha mavjud emas. Tez orada qo&apos;shiladi.</p>
      </div>
    );
  }

  const { turnir } = await searchParams;
  const active = competitions.find((c) => c.code === turnir) || competitions[0];
  const data = await apiGet(`/api/scores/standings/${active.code}`);
  const table = data?.table || [];
  const totalTeams = table.length;

  return (
    <div className="py-4 sm:py-8 space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
          <span>🏆</span> Turnir Jadvallari
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Natijalar real vaqt rejimida yangilanadi. Manba: football-data.org
        </p>
      </div>

      {/* League Selection Tabs */}
      <div className="flex flex-wrap gap-2 overflow-x-auto pb-2 hide-scrollbar">
        {competitions.map((c) => (
          <Link
            key={c.code}
            href={`/jadval?turnir=${c.code}`}
            className={`shrink-0 rounded-full border px-4 py-2 text-xs font-bold transition-all duration-200 ${
              c.code === active.code
                ? "border-emerald-500/25 bg-emerald-500/10 text-emerald-400 shadow-sm shadow-emerald-500/5"
                : "border-slate-900 bg-slate-950/40 text-slate-400 hover:border-slate-700 hover:text-white"
            }`}
          >
            {c.name}
          </Link>
        ))}
      </div>

      {/* Standings Table Card */}
      {table.length === 0 ? (
        <div className="rounded-2xl border border-slate-900 bg-slate-950/20 p-10 text-center text-slate-500">
          Bu turnir uchun jadval hali shakllanmadi (mavsum tanaffusda bo&apos;lishi mumkin).
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-900 bg-slate-950/30 backdrop-blur-sm">
          <table className="w-full text-xs sm:text-sm border-collapse">
            <thead>
              <tr className="border-b border-slate-900 bg-slate-950/50 text-[10px] uppercase tracking-wider text-slate-400 font-bold">
                <th className="px-3 py-3 text-left w-12">#</th>
                <th className="px-3 py-3 text-left">Jamoa</th>
                <th className="px-2.5 py-3 text-center w-10" title="O'ynadi">O&apos;</th>
                <th className="px-2.5 py-3 text-center w-10" title="Yutdi">G&apos;</th>
                <th className="px-2.5 py-3 text-center w-10" title="Durang">D</th>
                <th className="px-2.5 py-3 text-center w-10" title="Yutqazdi">M</th>
                <th className="px-2.5 py-3 text-center w-12" title="Gol farqi">Gol</th>
                <th className="px-4 py-3 text-center w-16 font-extrabold text-emerald-400">Ochko</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-900/60">
              {table.map((r) => (
                <tr
                  key={r.position}
                  className="hover:bg-slate-900/20 transition-colors duration-150"
                >
                  <td className={`py-3 ${getPositionBg(r.position, totalTeams)} font-bold`}>
                    <div className={getPositionIndicator(r.position, totalTeams)}>
                      {r.position}
                    </div>
                  </td>
                  <td className="px-3 py-3 font-semibold text-white">
                    {r.team}
                  </td>
                  <td className="px-2.5 py-3 text-center text-slate-400 font-medium">{r.played}</td>
                  <td className="px-2.5 py-3 text-center text-slate-400 font-medium">{r.won}</td>
                  <td className="px-2.5 py-3 text-center text-slate-400 font-medium">{r.draw}</td>
                  <td className="px-2.5 py-3 text-center text-slate-400 font-medium">{r.lost}</td>
                  <td className="px-2.5 py-3 text-center text-slate-400 font-semibold">{r.goal_diff}</td>
                  <td className="px-4 py-3 text-center font-extrabold text-white">{r.points}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Legend Indicators */}
      {table.length > 0 && (
        <div className="flex flex-wrap gap-x-6 gap-y-2.5 pt-2 text-[10px] text-slate-500 font-bold uppercase tracking-wider">
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
            <span>Chempionlar Ligasi</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-sky-500"></span>
            <span>Europa Ligasi</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-red-500"></span>
            <span>Chiqib ketish zonasi</span>
          </div>
        </div>
      )}
    </div>
  );
}
