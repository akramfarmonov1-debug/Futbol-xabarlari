"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { getFavoriteClub, saveFavoriteClub } from "../lib/favorites";

const DEFAULT_VISIBLE_ROWS = 8;

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
    indicator: "border-l-2 border-l-emerald-500 pl-1.5",
    color: "font-bold text-emerald-400",
  },
  champions: {
    indicator: "border-l-2 border-l-emerald-500 pl-1.5",
    color: "font-bold text-emerald-400",
  },
  europa: {
    indicator: "border-l-2 border-l-sky-500 pl-1.5",
    color: "font-bold text-sky-400",
  },
  playoff: {
    indicator: "border-l-2 border-l-amber-500 pl-1.5",
    color: "font-bold text-amber-400",
  },
  relegation: {
    indicator: "border-l-2 border-l-red-500 pl-1.5",
    color: "font-bold text-red-400",
  },
};

function getPositionStyle(code, position, total) {
  const zone = getZone(code, position, total);
  return zone
    ? ZONE_STYLES[zone]
    : { indicator: "pl-2", color: "text-slate-400" };
}

function formatGoalDiff(val) {
  const num = Number(val);
  if (Number.isNaN(num)) return val ?? "0";
  if (num > 0) return `+${num}`;
  return String(num);
}

export default function StandingsWidgetClient({ leagues, initialLeagueCode }) {
  const [activeCode, setActiveCode] = useState(
    initialLeagueCode || leagues[0]?.code || "UZB",
  );
  const [expanded, setExpanded] = useState(false);
  const [favoriteClub, setFavoriteClub] = useState(null);

  useEffect(() => {
    let animId = requestAnimationFrame(() => {
      const fav = getFavoriteClub();
      if (fav) {
        setFavoriteClub(fav);
        if (fav.leagueCode && !initialLeagueCode) {
          const found = leagues.some((l) => l.code === fav.leagueCode);
          if (found) setActiveCode(fav.leagueCode);
        }
      }
    });

    const handler = (e) => {
      setFavoriteClub(e.detail || null);
    };
    window.addEventListener("favorite_club_changed", handler);
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("favorite_club_changed", handler);
    };
  }, [leagues, initialLeagueCode]);

  const activeLeague =
    leagues.find((item) => item.code === activeCode) || leagues[0];

  if (!activeLeague) return null;

  const rows = activeLeague.table || [];
  const totalTeams = activeLeague.totalTeams || rows.length;
  const visibleRows = expanded ? rows : rows.slice(0, DEFAULT_VISIBLE_ROWS);
  const canExpand = rows.length > DEFAULT_VISIBLE_ROWS;

  const toggleFavorite = (teamName, leagueCode) => {
    if (favoriteClub?.name?.toLowerCase() === teamName.toLowerCase()) {
      saveFavoriteClub(null);
    } else {
      saveFavoriteClub({ name: teamName, leagueCode });
    }
  };

  return (
    <section
      aria-label="Turnir jadvali"
      className="overflow-hidden rounded-2xl border border-slate-800/80 bg-slate-950/60 p-4 shadow-2xl shadow-emerald-950/10 backdrop-blur-md"
    >
      {/* Header */}
      <div className="mb-3 flex items-center justify-between border-b border-slate-900/80 pb-2.5">
        <div className="flex items-center gap-2">
          <span className="text-sm" aria-hidden="true">
            🏆
          </span>
          <h2 className="text-xs font-extrabold uppercase tracking-wider text-slate-200">
            Turnir jadvali
          </h2>
        </div>
        <Link
          href={`/jadval?turnir=${activeLeague.code}`}
          className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 transition-colors hover:text-emerald-300"
        >
          To‘liq jadval →
        </Link>
      </div>

      {/* League Selector Tabs: 3 ustunli qulay va to'liq ko'rinadigan grid */}
      {leagues.length > 1 && (
        <div
          role="tablist"
          aria-label="Turnir tanlash"
          className="mb-3 grid grid-cols-3 gap-1.5"
        >
          {leagues.map((league) => {
            const isActive = league.code === activeLeague.code;
            return (
              <button
                key={league.code}
                type="button"
                role="tab"
                aria-selected={isActive}
                onClick={() => {
                  setActiveCode(league.code);
                  setExpanded(false);
                }}
                className={`inline-flex items-center justify-center gap-1 rounded-lg border px-1.5 py-1.5 text-[10.5px] font-bold transition-all duration-150 cursor-pointer ${
                  isActive
                    ? "border-emerald-500/40 bg-emerald-500/20 text-emerald-300 shadow-sm shadow-emerald-500/10"
                    : "border-slate-800/80 bg-slate-900/40 text-slate-400 hover:border-slate-700 hover:text-slate-200 hover:bg-slate-900/60"
                }`}
              >
                {league.badge ? (
                  <span className="relative h-3.5 w-3.5 shrink-0">
                    <Image
                      unoptimized
                      src={league.badge}
                      alt=""
                      fill
                      sizes="14px"
                      className="object-contain"
                    />
                  </span>
                ) : (
                  <span aria-hidden="true" className="text-[10px] leading-none">
                    {league.flag}
                  </span>
                )}
                <span className="truncate">{league.shortName}</span>
              </button>
            );
          })}
        </div>
      )}

      {/* Active League Subtitle */}
      <div className="mb-2 flex items-center justify-between px-1 text-[10px] font-bold uppercase tracking-wider text-slate-500">
        <span className="truncate text-emerald-400/85">
          {activeLeague.competition}
        </span>
        {activeLeague.season && (
          <span className="shrink-0 text-slate-600">
            {activeLeague.season}
          </span>
        )}
      </div>

      {/* Standings Mini Table */}
      <div className="overflow-hidden rounded-xl border border-slate-900/80 bg-slate-950/40">
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr className="border-b border-slate-900 bg-slate-950/70 text-[10px] font-bold uppercase tracking-wider text-slate-500">
              <th className="w-7 py-2 pl-2 text-left">#</th>
              <th className="py-2 pr-1 text-left">Jamoa</th>
              <th className="w-7 py-2 text-center" title="O‘yinlar soni">
                O‘
              </th>
              <th className="w-8 py-2 text-center" title="To‘plar nisbati">
                +/-
              </th>
              <th
                className="w-10 py-2 pr-2.5 text-right font-extrabold text-emerald-400"
                title="Ochko"
              >
                Och
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-900/50">
            {visibleRows.map((row) => {
              const posStyle = getPositionStyle(
                activeLeague.code,
                row.position,
                totalTeams,
              );
              const isFav =
                favoriteClub?.name?.toLowerCase() === row.team?.toLowerCase();

              return (
                <tr
                  key={`${activeLeague.code}-${row.position}-${row.team}`}
                  className={`transition-colors duration-150 ${
                    isFav
                      ? "bg-emerald-500/10 hover:bg-emerald-500/15"
                      : "hover:bg-slate-900/35"
                  }`}
                >
                  <td className={`py-2 text-[11px] ${posStyle.color}`}>
                    <div className={posStyle.indicator}>{row.position}</div>
                  </td>
                  <td className="py-2 pr-1 font-semibold text-slate-200 max-w-0">
                    <div className="flex min-w-0 items-center gap-1.5">
                      {row.crest ? (
                        <span className="relative h-5 w-5 shrink-0">
                          <Image
                            unoptimized
                            src={row.crest}
                            alt={`${row.team} logotipi`}
                            fill
                            sizes="20px"
                            className="object-contain"
                          />
                        </span>
                      ) : (
                        <span
                          aria-hidden="true"
                          className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-slate-900 text-[9px] font-bold text-slate-500"
                        >
                          {row.team?.slice(0, 1) || "?"}
                        </span>
                      )}
                      <span
                        className={`truncate text-xs ${
                          isFav ? "font-bold text-emerald-300" : ""
                        }`}
                        title={row.team}
                      >
                        {row.team}
                      </span>
                      <button
                        type="button"
                        aria-label={
                          isFav
                            ? `${row.team}ni sevimlilardan chiqarish`
                            : `${row.team}ni sevimli jamoam deb belgilash`
                        }
                        title={isFav ? "Sevimli jamoangiz" : "Sevimli qilish"}
                        onClick={() =>
                          toggleFavorite(row.team, activeLeague.code)
                        }
                        className={`shrink-0 text-[11px] transition-transform hover:scale-125 cursor-pointer ${
                          isFav ? "opacity-100" : "opacity-20 hover:opacity-100"
                        }`}
                      >
                        ⭐
                      </button>
                    </div>
                  </td>
                  <td className="py-2 text-center text-[11px] font-medium text-slate-400">
                    {row.played}
                  </td>
                  <td className="py-2 text-center text-[11px] font-medium text-slate-400">
                    {formatGoalDiff(row.goal_diff)}
                  </td>
                  <td
                    className={`py-2 pr-2.5 text-right text-xs font-extrabold ${
                      isFav ? "text-emerald-300" : "text-white"
                    }`}
                  >
                    {row.points}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Footer Actions */}
      <div className="mt-3 flex items-center justify-between gap-2 pt-0.5">
        {canExpand ? (
          <button
            type="button"
            onClick={() => setExpanded((prev) => !prev)}
            className="text-[11px] font-bold text-slate-400 transition-colors hover:text-white cursor-pointer"
          >
            {expanded
              ? "Qisqartirish ↑"
              : `Yana ko‘rsatish (${totalTeams} jamoa) ↓`}
          </button>
        ) : (
          <span className="text-[10px] text-slate-600">
            Jami {totalTeams} jamoa
          </span>
        )}

        <Link
          href={`/jadval?turnir=${activeLeague.code}`}
          className="inline-flex items-center gap-1 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-[11px] font-bold text-emerald-400 transition-all hover:border-emerald-500/40 hover:bg-emerald-500 hover:text-slate-950"
        >
          <span>Batafsil</span>
          <span aria-hidden="true">→</span>
        </Link>
      </div>
    </section>
  );
}
