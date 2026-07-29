import Image from "next/image";
import Link from "next/link";
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

function TeamCrest({ src, name }) {
  if (!src) {
    return (
      <span
        aria-hidden="true"
        className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-slate-800 bg-slate-900 text-[9px] font-black text-slate-500"
      >
        {name?.slice(0, 1) || "?"}
      </span>
    );
  }

  return (
    <span className="relative h-6 w-6 shrink-0">
      <Image
        src={src}
        alt={`${name} logotipi`}
        fill
        sizes="24px"
        className="object-contain"
      />
    </span>
  );
}

function MatchRow({ match }) {
  const played =
    match.home_score !== null && match.away_score !== null;

  return (
    <div className="grid grid-cols-[minmax(0,1fr)_54px_minmax(0,1fr)] items-center gap-2 rounded-xl px-2 py-2.5 transition-colors duration-150 hover:bg-slate-900/30">
      <span
        className="flex min-w-0 items-center justify-end gap-2"
        title={match.home}
      >
        <span className="truncate text-right text-xs font-semibold text-slate-200">
          {match.home}
        </span>
        <TeamCrest src={match.home_crest} name={match.home} />
      </span>

      <span className="flex justify-center">
        {played ? (
          <span
            className={`inline-flex min-w-12 items-center justify-center rounded-lg px-2 py-1 text-xs font-black ${
              match.is_live
                ? "animate-pulse border border-red-500/30 bg-red-500/10 text-red-400"
                : "border border-slate-700/70 bg-slate-800 text-white"
            }`}
          >
            {match.home_score} : {match.away_score}
          </span>
        ) : (
          <span className="rounded-lg border border-slate-800/80 bg-slate-900/60 px-2 py-1 text-[10px] font-bold tracking-wider text-emerald-400">
            {timeUz(match.kickoff)}
          </span>
        )}
      </span>

      <span
        className="flex min-w-0 items-center gap-2"
        title={match.away}
      >
        <TeamCrest src={match.away_crest} name={match.away} />
        <span className="truncate text-left text-xs font-semibold text-slate-200">
          {match.away}
        </span>
      </span>
    </div>
  );
}

export default async function LiveScores() {
  const [groups, profiles] = await Promise.all([
    apiGet("/api/scores/today"),
    apiGet("/api/scores/league-profiles"),
  ]);

  if (!groups || groups.length === 0) return null;

  const profileByCode = Object.fromEntries(
    (profiles || []).map((profile) => [profile.code, profile]),
  );

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-800/80 bg-slate-950/60 p-4 shadow-2xl shadow-emerald-950/10 backdrop-blur-md">
      <div className="mb-4 flex items-center justify-between border-b border-slate-900/80 pb-2">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          </span>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Bugungi o&apos;yinlar
          </h2>
        </div>
        <Link
          href="/jadval"
          className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 transition-colors hover:text-emerald-300"
        >
          Jadvallar →
        </Link>
      </div>

      <div className="space-y-4">
        {groups.map((group) => {
          const profile = profileByCode[group.code];
          return (
            <div
              key={group.code}
              className="border-b border-slate-900/60 pb-3 last:border-0 last:pb-0"
            >
              <div className="mb-2 flex items-center gap-2 text-[9px] font-bold uppercase tracking-widest text-emerald-400/80">
                {profile?.badge && (
                  <span className="relative h-5 w-5">
                    <Image
                      src={profile.badge}
                      alt={`${group.competition} belgisi`}
                      fill
                      sizes="20px"
                      className="object-contain"
                    />
                  </span>
                )}
                {group.competition}
              </div>
              <div className="space-y-1">
                {group.matches.map((match, index) => (
                  <MatchRow
                    key={`${match.home}-${match.away}-${match.kickoff || index}`}
                    match={match}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <p className="mt-3 border-t border-slate-900/70 pt-3 text-[9px] text-slate-600">
        Liga vizuallari: TheSportsDB
      </p>
    </section>
  );
}
