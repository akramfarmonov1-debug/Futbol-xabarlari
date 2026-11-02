import Image from "next/image";
import Link from "next/link";
import { apiGet } from "../lib/api";
import NotificationBell from "./NotificationBell";

function UzFlag({ className = "h-3 w-4.5" }) {
  return (
    <svg className={`${className} rounded-xs inline-block shadow-xs shrink-0`} viewBox="0 0 500 250" fill="none">
      <rect width="500" height="83.33" fill="#1EB53A" y="166.67" />
      <rect width="500" height="83.33" fill="#FFFFFF" y="83.33" />
      <rect width="500" height="83.33" fill="#0099B5" />
      <rect width="500" height="5" fill="#CE1126" y="80.83" />
      <rect width="500" height="5" fill="#CE1126" y="164.17" />
      <circle cx="50" cy="41.67" r="25" fill="#FFFFFF" />
      <circle cx="58" cy="41.67" r="25" fill="#0099B5" />
    </svg>
  );
}

export default async function Header() {
  const categories = (await apiGet("/api/categories")) || [];

  return (
    <header className="sticky top-0 z-30 w-full border-b border-slate-900/90 bg-slate-950/95 backdrop-blur-md">
      <div className="mx-auto max-w-6xl px-4 py-3.5 flex flex-col gap-3.5">
        {/* Top Row */}
        <div className="flex items-center justify-between gap-4">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-green-600 shadow-lg shadow-emerald-500/20 group-hover:scale-105 transition-all duration-300">
              <Image src="/logo.svg" alt="Futbol Xabar" width={30} height={30} />
            </div>
            <span className="text-xl font-bold tracking-tight text-white">
              Futbol <span className="text-gradient-emerald">Xabar</span>
            </span>
          </Link>

          {/* Actions & Search */}
          <div className="flex items-center gap-3">
            {/* Desktop Telegram Links */}
            <div className="hidden lg:flex items-center gap-3 text-xs font-semibold">
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
                className="w-36 sm:w-52 rounded-full border border-slate-800 bg-slate-900/60 px-4 py-2 pl-9 text-xs text-white outline-none focus:border-emerald-500 focus:bg-slate-900/90 transition-all duration-200"
              />
              <span className="absolute left-3.5 text-slate-500 text-xs">🔍</span>
            </form>

            {/* Push Notification Bell */}
            <NotificationBell />
          </div>
        </div>

        {/* Categories Bar — silliq o'ng gradientli gorizontal scroll */}
        <div className="relative max-w-full">
          <nav className="flex max-w-full flex-nowrap items-center gap-2 overflow-x-auto pb-1 pr-6 hide-scrollbar custom-scrollbar">
            <Link
              href="/legionerlar"
              className="flex shrink-0 items-center gap-1.5 rounded-full border border-sky-500/25 bg-sky-500/10 px-3.5 py-1.5 text-xs font-semibold text-sky-400 hover:bg-sky-500 hover:text-slate-950 transition-all duration-200 shadow-sm shadow-sky-500/5"
            >
              <UzFlag className="h-3 w-4.5" />
              <span>Legionerlar</span>
            </Link>

            <Link
              href="/jadval"
              className="flex shrink-0 items-center gap-1.5 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3.5 py-1.5 text-xs font-semibold text-emerald-400 hover:bg-emerald-500 hover:text-slate-950 transition-all duration-200 shadow-sm shadow-emerald-500/5"
            >
              <span>🏆</span>
              <span>Turnir Jadvali</span>
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
          {/* O'ng tomondagi yumshoq gradient soyasi */}
          <div className="pointer-events-none absolute right-0 top-0 bottom-1 w-10 bg-gradient-to-l from-slate-950 via-slate-950/80 to-transparent"></div>
        </div>
      </div>
    </header>
  );
}
