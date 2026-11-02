import { apiGet } from "../lib/api";
import { getClubLogo } from "../lib/clubs";
import StandingsWidgetClient from "./StandingsWidgetClient";

const WIDGET_LEAGUES = [
  {
    code: "UZB",
    shortName: "Superliga",
    flag: "🇺🇿",
    defaultTitle: "O‘zbekiston Superligasi",
  },
  {
    code: "PL",
    shortName: "APL",
    flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    defaultTitle: "Angliya Premyer-ligasi",
  },
  {
    code: "PD",
    shortName: "La Liga",
    flag: "🇪🇸",
    defaultTitle: "Ispaniya La Ligasi",
  },
  {
    code: "SA",
    shortName: "A Seriya",
    flag: "🇮🇹",
    defaultTitle: "Italiya A Seriyasi",
  },
  {
    code: "BL1",
    shortName: "Bundesliga",
    flag: "🇩🇪",
    defaultTitle: "Germaniya Bundesligasi",
  },
  {
    code: "CL",
    shortName: "ChL",
    flag: "🇪🇺",
    defaultTitle: "UEFA Chempionlar ligasi",
  },
];

export default async function StandingsWidget({ initialLeagueCode }) {
  const [profiles, ...standingsResults] = await Promise.all([
    apiGet("/api/scores/league-profiles"),
    ...WIDGET_LEAGUES.map((league) =>
      apiGet(`/api/scores/standings/${league.code}`),
    ),
  ]);

  const profileByCode = Object.fromEntries(
    (profiles || []).map((profile) => [profile.code, profile]),
  );

  const leagues = WIDGET_LEAGUES.map((meta, idx) => {
    const data = standingsResults[idx];
    const table = data?.table || [];
    if (!table.length) return null;

    const profile = profileByCode[meta.code];
    return {
      code: meta.code,
      shortName: meta.shortName,
      flag: meta.flag,
      competition: data?.competition || meta.defaultTitle,
      season: data?.season || null,
      badge: profile?.badge || null,
      totalTeams: table.length,
      table: table.map((row) => ({
        position: row.position,
        team: row.team,
        crest: getClubLogo(row.team, row.crest) || null,
        played: row.played,
        points: row.points,
        goal_diff: row.goal_diff,
      })),
    };
  }).filter(Boolean);

  if (!leagues.length) return null;

  return (
    <StandingsWidgetClient
      leagues={leagues}
      initialLeagueCode={initialLeagueCode}
    />
  );
}
