import { apiGet } from "../lib/api";

function timeUz(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleTimeString("uz-UZ", {
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "Asia/Tashkent",
    });
  } catch {
    return "";
  }
}

function MatchRow({ m }) {
  const played = m.home_score !== null && m.away_score !== null;
  return (
    <div className="flex items-center justify-between py-2.5 hover:bg-slate-900/20 px-1 rounded-lg transition-colors duration-150">
      {/* Home Team */}
      <span className="w-[42%] truncate text-right text-xs font-semibold text-slate-200" title={m.home}>
        {m.home}
      </span>
      
      {/* Score / Time Box */}
      <span className="w-[16%] flex justify-center">
        {played ? (
          <span
            className={`inline-flex items-center justify-center rounded px-2 py-0.5 text-xs font-bold ${
              m.is_live
                ? "bg-red-500/10 text-red-400 border border-red-500/20 animate-pulse"
                : "bg-slate-800 text-slate-200"
            }`}
          >
            {m.home_score} : {m.away_score}
          </span>
        ) : (
          <span className="rounded bg-slate-900/60 border border-slate-800/80 px-2 py-0.5 text-[10px] font-bold text-emerald-400 tracking-wider">
            {timeUz(m.kickoff)}
          </span>
        )}
      </span>
      
      {/* Away Team */}
      <span className="w-[42%] truncate text-left text-xs font-semibold text-slate-200" title={m.away}>
        {m.away}
      </span>
    </div>
  );
}

export default async function LiveScores() {
  const groups = await apiGet("/api/scores/today");

  if (!groups || groups.length === 0) return null;

  return (
    <section className="rounded-2xl border border-slate-900 bg-slate-950/40 p-4 backdrop-blur-md">
      <div className="mb-4 flex items-center justify-between border-b border-slate-900/80 pb-2">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300">⚽ Bugungi O&apos;yinlar</h2>
        </div>
        <a href="/jadval" className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 hover:text-emerald-300 transition-colors">
          Jadvallar →
        </a>
      </div>
      <div className="space-y-4">
        {groups.map((g) => (
          <div key={g.code} className="border-b border-slate-900/40 last:border-0 pb-3 last:pb-0">
            <div className="mb-2 text-[9px] font-bold uppercase tracking-widest text-emerald-500/70">
              🏆 {g.competition}
            </div>
            <div className="space-y-1">
              {g.matches.map((m, i) => (
                <MatchRow key={i} m={m} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
