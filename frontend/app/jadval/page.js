import Image from "next/image";
import Link from "next/link";
import { apiGet } from "../../lib/api";

export const metadata = {
  title: "Turnir jadvallari",
  description:
    "O'zbekiston Superligasi, Angliya Premyer-ligasi, La Liga, Seriya A, Bundesliga va Chempionlar ligasi jadvallari.",
  alternates: { canonical: "/jadval" },
};

export const revalidate = 3600;

function getZone(code, position, total) {
  if (code === "UZB") {
    if (position === 1) return "leader";
    if (position >= 12 && position <= 15) return "playoff";
    if (position === 16) return "relegation";
    return null;
  }

  if (code === "CL") {
    if (position <= 8) return "champions";
    if (position <= 24) return "europa";
    return null;
  }

  if (position <= 4) return "champions";
  if (position === 5) return "europa";
  if (code === "BL1" && position === total - 2) return "playoff";
  if (position >= total - 2) return "relegation";
  return null;
}

const ZONE_STYLES = {
  leader: {
    indicator: "border-l-[3px] border-l-emerald-500 pl-2",
    color: "font-bold text-emerald-400",
  },
  champions: {
    indicator: "border-l-[3px] border-l-emerald-500 pl-2",
    color: "font-bold text-emerald-400",
  },
  europa: {
    indicator: "border-l-[3px] border-l-sky-500 pl-2",
    color: "font-bold text-sky-400",
  },
  playoff: {
    indicator: "border-l-[3px] border-l-amber-500 pl-2",
    color: "font-bold text-amber-400",
  },
  relegation: {
    indicator: "border-l-[3px] border-l-red-500 pl-2",
    color: "font-bold text-red-400",
  },
};

function getPositionStyle(code, position, total) {
  const zone = getZone(code, position, total);
  return zone
    ? ZONE_STYLES[zone]
    : { indicator: "pl-3", color: "text-slate-400" };
}

function getLegend(code) {
  if (code === "UZB") {
    return [
      { color: "bg-emerald-500", label: "Peshqadam" },
      { color: "bg-amber-500", label: "12–15-o‘rin: pley-off" },
      { color: "bg-red-500", label: "16-o‘rin: Proligaga tushadi" },
    ];
  }
  if (code === "CL") {
    return [
      { color: "bg-emerald-500", label: "1/8 finalga to‘g‘ridan-to‘g‘ri" },
      { color: "bg-sky-500", label: "Pley-off bosqichi" },
    ];
  }
  return [
    { color: "bg-emerald-500", label: "Chempionlar Ligasi" },
    { color: "bg-sky-500", label: "Europa Ligasi" },
    { color: "bg-red-500", label: "Quyi zona" },
  ];
}

function LeagueBadge({ profile, name, size = 20 }) {
  if (!profile?.badge) return null;

  return (
    <span
      className="relative inline-block shrink-0 align-middle"
      style={{ width: size, height: size }}
    >
      <Image
        src={profile.badge}
        alt={`${name} belgisi`}
        fill
        sizes={`${size}px`}
        className="object-contain"
      />
    </span>
  );
}

function TeamIdentity({ row }) {
  return (
    <div className="flex min-w-40 items-center gap-3">
      {row.crest ? (
        <span className="relative h-7 w-7 shrink-0">
          <Image
            src={row.crest}
            alt={`${row.team} logotipi`}
            fill
            sizes="28px"
            className="object-contain"
          />
        </span>
      ) : (
        <span
          aria-hidden="true"
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-900 text-[10px] text-slate-500"
        >
          {row.team?.slice(0, 1)}
        </span>
      )}
      <span>{row.team}</span>
    </div>
  );
}

export default async function StandingsPage({ searchParams }) {
  const competitions = (await apiGet("/api/scores/competitions")) || [];

  if (competitions.length === 0) {
    return (
      <div className="py-24 text-center text-slate-400">
        <h1 className="mb-3 text-2xl font-extrabold text-white">
          Turnir jadvallari
        </h1>
        <p className="text-xs">
          Jadval ma&apos;lumotlari hozircha mavjud emas. Tez orada
          qo&apos;shiladi.
        </p>
      </div>
    );
  }

  const { turnir } = await searchParams;
  const active =
    competitions.find((competition) => competition.code === turnir) ||
    competitions[0];

  const [data, profiles] = await Promise.all([
    apiGet(`/api/scores/standings/${active.code}`),
    apiGet("/api/scores/league-profiles"),
  ]);

  const table = data?.table || [];
  const totalTeams = table.length;
  const profileByCode = Object.fromEntries(
    (profiles || []).map((profile) => [profile.code, profile]),
  );
  const activeProfile = profileByCode[active.code];
  const leagueArtwork =
    activeProfile?.fanart || activeProfile?.banner || activeProfile?.poster;
  const leader = table[0];
  const totalGames = Math.round(
    table.reduce(
      (sum, row) => sum + (Number(row.played) || 0),
      0,
    ) / 2,
  );
  const legend = getLegend(active.code);

  return (
    <div className="space-y-6 py-4 sm:py-8">
      <section className="relative isolate overflow-hidden rounded-3xl border border-slate-800 bg-slate-950 px-5 py-7 shadow-2xl shadow-emerald-950/20 sm:px-8 sm:py-10">
        {leagueArtwork && (
          <Image
            src={leagueArtwork}
            alt=""
            fill
            priority
            sizes="(max-width: 1024px) 100vw, 1100px"
            className="object-cover opacity-30"
          />
        )}
        <div className="absolute inset-0 bg-gradient-to-r from-slate-950 via-slate-950/90 to-emerald-950/45" />

        <div className="relative z-10 flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div className="relative flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-white/95 p-3 shadow-xl">
              {activeProfile?.badge ? (
                <Image
                  src={activeProfile.badge}
                  alt={`${active.name} belgisi`}
                  fill
                  sizes="80px"
                  className="object-contain p-3"
                />
              ) : (
                <span className="text-3xl" aria-hidden="true">
                  🏆
                </span>
              )}
            </div>

            <div>
              <p className="mb-1 text-[10px] font-black uppercase tracking-[0.25em] text-emerald-400">
                Futbol markazi
              </p>
              <h1 className="text-2xl font-black tracking-tight text-white sm:text-4xl">
                {active.name}
              </h1>
              <p className="mt-2 text-xs text-slate-400">
                {activeProfile?.country ||
                  (active.code === "UZB" ? "Uzbekistan" : "Yevropa")}
                {activeProfile?.formed_year
                  ? ` · ${activeProfile.formed_year}-yildan`
                  : ""}
                {data?.season ? ` · ${data.season}-yilgi mavsum` : ""}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2 sm:min-w-72">
            <div className="rounded-2xl border border-white/10 bg-slate-950/65 p-3 text-center backdrop-blur">
              <strong className="block text-lg font-black text-white">
                {totalTeams || "—"}
              </strong>
              <span className="text-[9px] font-bold uppercase tracking-wider text-slate-500">
                Jamoa
              </span>
            </div>
            <div className="rounded-2xl border border-white/10 bg-slate-950/65 p-3 text-center backdrop-blur">
              <strong className="block text-lg font-black text-white">
                {totalGames || "—"}
              </strong>
              <span className="text-[9px] font-bold uppercase tracking-wider text-slate-500">
                O‘yin
              </span>
            </div>
            <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-3 text-center backdrop-blur">
              <strong className="block truncate text-sm font-black text-emerald-300">
                {leader?.team || "—"}
              </strong>
              <span className="text-[9px] font-bold uppercase tracking-wider text-emerald-500/70">
                Peshqadam
              </span>
            </div>
          </div>
        </div>
      </section>

      <nav
        aria-label="Turnir tanlash"
        className="flex flex-wrap gap-2 overflow-x-auto pb-2 hide-scrollbar"
      >
        {competitions.map((competition) => (
          <Link
            key={competition.code}
            href={`/jadval?turnir=${competition.code}`}
            className={`inline-flex shrink-0 items-center rounded-full border px-4 py-2 text-xs font-bold transition-all duration-200 ${
              competition.code === active.code
                ? "border-emerald-500/25 bg-emerald-500/10 text-emerald-400 shadow-sm shadow-emerald-500/5"
                : "border-slate-900 bg-slate-950/40 text-slate-400 hover:border-slate-700 hover:text-white"
            }`}
          >
            <LeagueBadge
              profile={profileByCode[competition.code]}
              name={competition.name}
              size={16}
            />
            <span className={profileByCode[competition.code]?.badge ? "ml-2" : ""}>
              {competition.name}
            </span>
          </Link>
        ))}
      </nav>

      {table.length === 0 ? (
        <div className="rounded-2xl border border-slate-900 bg-slate-950/20 p-10 text-center text-slate-500">
          Bu turnir uchun jadval hali shakllanmadi — mavsum tanaffusda
          bo&apos;lishi mumkin.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-900 bg-slate-950/30 backdrop-blur-sm">
          <table className="w-full border-collapse text-xs sm:text-sm">
            <thead>
              <tr className="border-b border-slate-900 bg-slate-950/50 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                <th className="w-12 px-3 py-3 text-left">#</th>
                <th className="px-3 py-3 text-left">Jamoa</th>
                <th className="w-10 px-2.5 py-3 text-center" title="O‘ynadi">
                  O&apos;
                </th>
                <th className="w-10 px-2.5 py-3 text-center" title="Yutdi">
                  G&apos;
                </th>
                <th className="w-10 px-2.5 py-3 text-center" title="Durang">
                  D
                </th>
                <th className="w-10 px-2.5 py-3 text-center" title="Yutqazdi">
                  M
                </th>
                <th className="w-12 px-2.5 py-3 text-center" title="Gol farqi">
                  Gol
                </th>
                <th className="w-16 px-4 py-3 text-center font-extrabold text-emerald-400">
                  Ochko
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-900/60">
              {table.map((row) => {
                const positionStyle = getPositionStyle(
                  active.code,
                  row.position,
                  totalTeams,
                );
                return (
                  <tr
                    key={row.position}
                    className="transition-colors duration-150 hover:bg-slate-900/20"
                  >
                    <td
                      className={`py-3 font-bold ${positionStyle.color}`}
                    >
                      <div className={positionStyle.indicator}>
                        {row.position}
                      </div>
                    </td>
                  <td className="px-3 py-3 font-semibold text-white">
                    <TeamIdentity row={row} />
                  </td>
                  <td className="px-2.5 py-3 text-center font-medium text-slate-400">
                    {row.played}
                  </td>
                  <td className="px-2.5 py-3 text-center font-medium text-slate-400">
                    {row.won}
                  </td>
                  <td className="px-2.5 py-3 text-center font-medium text-slate-400">
                    {row.draw}
                  </td>
                  <td className="px-2.5 py-3 text-center font-medium text-slate-400">
                    {row.lost}
                  </td>
                  <td className="px-2.5 py-3 text-center font-semibold text-slate-400">
                    {row.goal_diff}
                  </td>
                  <td className="px-4 py-3 text-center font-extrabold text-white">
                    {row.points}
                  </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {table.length > 0 && (
        <div className="flex flex-col gap-4 pt-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap gap-x-6 gap-y-2.5 text-[10px] font-bold uppercase tracking-wider text-slate-500">
            {legend.map((item) => (
              <div key={item.label} className="flex items-center gap-1.5">
                <span className={`h-2 w-2 rounded-full ${item.color}`} />
                <span>{item.label}</span>
              </div>
            ))}
          </div>
          <div className="text-right text-[10px] leading-relaxed text-slate-600">
            <p>
              Natijalar:{" "}
              {data?.source === "PFL.UZ" ? (
                <a
                  href="https://pfl.uz"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline decoration-slate-700 underline-offset-2 hover:text-emerald-400"
                >
                  PFL.UZ rasmiy ma’lumoti
                </a>
              ) : (
                data?.source || "sport ma’lumotlari API"
              )}
              {" · "}Vizuallar: TheSportsDB
            </p>
            <p>Jadval har soatda yangilanadi</p>
          </div>
        </div>
      )}
    </div>
  );
}
