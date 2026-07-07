import Link from "next/link";
import { apiGet } from "../../lib/api";

export const metadata = {
  title: "Turnir jadvallari",
  description:
    "Angliya Premyer-ligasi, La Liga, Seriya A, Bundesliga va Chempionlar ligasi turnir jadvallari — jonli yangilanadi.",
  alternates: { canonical: "/jadval" },
};

export const revalidate = 3600;

export default async function StandingsPage({ searchParams }) {
  const competitions = (await apiGet("/api/scores/competitions")) || [];

  // API kaliti sozlanmagan — jadval mavjud emas
  if (competitions.length === 0) {
    return (
      <div className="py-16 text-center text-slate-400">
        <h1 className="mb-3 text-2xl font-bold text-white">Turnir jadvallari</h1>
        <p>Jadval ma&apos;lumotlari hozircha mavjud emas. Tez orada qo&apos;shiladi.</p>
      </div>
    );
  }

  const { turnir } = await searchParams;
  const active = competitions.find((c) => c.code === turnir) || competitions[0];
  const data = await apiGet(`/api/scores/standings/${active.code}`);
  const table = data?.table || [];

  return (
    <div className="py-8">
      <h1 className="mb-5 text-2xl font-bold">🏆 Turnir jadvallari</h1>

      <div className="mb-6 flex flex-wrap gap-2">
        {competitions.map((c) => (
          <Link
            key={c.code}
            href={`/jadval?turnir=${c.code}`}
            className={`rounded-full border px-3 py-1 text-sm transition-colors ${
              c.code === active.code
                ? "border-green-500 bg-green-500/10 text-green-400"
                : "border-slate-700 text-slate-300 hover:border-green-500 hover:text-white"
            }`}
          >
            {c.name}
          </Link>
        ))}
      </div>

      {table.length === 0 ? (
        <p className="text-slate-400">
          Bu turnir uchun jadval hali mavjud emas (mavsum boshlanmagan bo&apos;lishi mumkin).
        </p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-sm">
            <thead className="bg-slate-900/60 text-slate-400">
              <tr>
                <th className="px-3 py-2 text-left">#</th>
                <th className="px-3 py-2 text-left">Jamoa</th>
                <th className="px-2 py-2 text-center" title="O'ynadi">O</th>
                <th className="px-2 py-2 text-center" title="Yutdi">Yu</th>
                <th className="px-2 py-2 text-center" title="Durang">D</th>
                <th className="px-2 py-2 text-center" title="Yutqazdi">M</th>
                <th className="px-2 py-2 text-center" title="Gol farqi">±</th>
                <th className="px-2 py-2 text-center font-bold">Ochko</th>
              </tr>
            </thead>
            <tbody>
              {table.map((r) => (
                <tr
                  key={r.position}
                  className="border-t border-slate-800/60 hover:bg-slate-900/40"
                >
                  <td className="px-3 py-2 text-slate-400">{r.position}</td>
                  <td className="px-3 py-2 font-medium text-white">{r.team}</td>
                  <td className="px-2 py-2 text-center text-slate-300">{r.played}</td>
                  <td className="px-2 py-2 text-center text-slate-300">{r.won}</td>
                  <td className="px-2 py-2 text-center text-slate-300">{r.draw}</td>
                  <td className="px-2 py-2 text-center text-slate-300">{r.lost}</td>
                  <td className="px-2 py-2 text-center text-slate-300">{r.goal_diff}</td>
                  <td className="px-2 py-2 text-center font-bold text-white">{r.points}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="mt-4 text-xs text-slate-500">
        Ma&apos;lumotlar manbasi: football-data.org · soatiga bir marta yangilanadi
      </p>
    </div>
  );
}
