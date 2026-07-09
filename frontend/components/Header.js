import Link from "next/link";
import { apiGet } from "../lib/api";

export default async function Header() {
  const categories = (await apiGet("/api/categories")) || [];

  return (
    <header className="sticky top-0 z-30 w-full border-b border-slate-900 bg-slate-950/80 backdrop-blur-md">
      <div className="mx-auto max-w-6xl px-4 py-4 flex flex-col gap-4">
        {/* Top Row */}
        <div className="flex items-center justify-between gap-4">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-green-600 shadow-lg shadow-emerald-500/20 group-hover:scale-105 transition-all duration-300">
              <img src="/logo.svg" alt="Logo" width={28} height={28} className="brightness-0 invert" />
            </div>
            <span className="text-xl font-bold tracking-tight text-white">
              Futbol <span className="text-gradient-emerald">Xabar</span>
            </span>
          </Link>

          {/* Actions & Search */}
          <div className="flex items-center gap-3">
            {/* Desktop Telegram Links */}
            <div className="hidden lg:flex items-center gap-4 text-xs font-semibold">
              <a
                href="https://t.me/futbolxabarida"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 rounded-full border border-slate-800 bg-slate-900/40 px-3.5 py-1.5 text-slate-300 hover:border-sky-500/30 hover:text-sky-400 hover:bg-slate-900 transition-all duration-200"
              >
                <span className="h-2 w-2 rounded-full bg-sky-400"></span>
                📢 Telegram Kanal
              </a>
              <a
                href="https://t.me/Futbolxabari_bot"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 rounded-full border border-slate-800 bg-slate-900/40 px-3.5 py-1.5 text-slate-300 hover:border-emerald-500/30 hover:text-emerald-400 hover:bg-slate-900 transition-all duration-200"
              >
                <span className="h-2 w-2 rounded-full bg-emerald-400"></span>
                🤖 Telegram Bot
              </a>
            </div>

            {/* Search Input */}
            <form action="/qidiruv" className="relative flex items-center">
              <input
                name="q"
                type="text"
                placeholder="Qidiruv..."
                className="w-40 sm:w-56 rounded-full border border-slate-800 bg-slate-900/60 px-4 py-2 pl-9 text-xs text-white outline-none focus:border-emerald-500 focus:bg-slate-900/90 transition-all duration-200"
              />
              <span className="absolute left-3.5 text-slate-500 text-xs">🔍</span>
            </form>
          </div>
        </div>

        {/* Categories Bar */}
        <nav className="flex items-center gap-2 overflow-x-auto pb-1 hide-scrollbar custom-scrollbar sm:overflow-visible">
          <Link
            href="/jadval"
            className="flex shrink-0 items-center gap-1 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-4 py-1.5 text-xs font-semibold text-emerald-400 hover:bg-emerald-500 hover:text-slate-950 transition-all duration-200 shadow-sm shadow-emerald-500/5"
          >
            🏆 Turnir Jadvali
          </Link>
          
          <div className="h-4 w-px bg-slate-800 shrink-0"></div>

          {categories.map((cat) => (
            <Link
              key={cat.slug}
              href={`/kategoriya/${cat.slug}`}
              className="shrink-0 rounded-full border border-slate-800 bg-slate-900/20 px-3.5 py-1.5 text-xs font-medium text-slate-300 hover:border-slate-700 hover:text-white hover:bg-slate-900/40 transition-all duration-200"
            >
              {cat.name}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
