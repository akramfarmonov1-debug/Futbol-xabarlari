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
    <div className="flex items-center gap-2 py-2 text-sm">
      <span className="flex-1 truncate text-right text-slate-200">{m.home}</span>
      <span className="min-w-[52px] text-center">
        {played ? (
          <span
            className={
              m.is_live
                ? "rounded bg-green-500/20 px-2 py-0.5 font-bold text-green-400"
                : "font-bold text-white"
            }
          >
            {m.home_score}:{m.away_score}
          </span>
        ) : (
          <span className="text-xs text-slate-500">{timeUz(m.kickoff)}</span>
        )}
      </span>
      <span className="flex-1 truncate text-slate-200">{m.away}</span>
    </div>
  );
}

export default async function LiveScores() {
  const groups = await apiGet("/api/scores/today");

  // API kaliti yo'q yoki bugun o'yin yo'q — blokni umuman ko'rsatmaymiz
  if (!groups || groups.length === 0) return null;

  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-bold">⚽ Bugungi o&apos;yinlar</h2>
        <a href="/jadval" className="text-xs text-green-400 hover:underline">
          Jadval →
        </a>
      </div>
      <div className="space-y-4">
        {groups.map((g) => (
          <div key={g.code}>
            <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
              {g.competition}
            </div>
            <div className="divide-y divide-slate-800/60">
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
