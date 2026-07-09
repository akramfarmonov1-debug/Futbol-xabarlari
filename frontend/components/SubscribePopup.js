"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "futbolxabar_popup_closed_at";
const SHOW_DELAY_MS = 10_000; // 10 soniyadan keyin chiqadi
const COOLDOWN_MS = 3 * 24 * 60 * 60 * 1000; // yopilgach 3 kun ko'rinmaydi

export default function SubscribePopup() {
  const [visible, setVisible] = useState(false);
  const [installEvent, setInstallEvent] = useState(null);

  useEffect(() => {
    if (window.matchMedia("(display-mode: standalone)").matches) return;

    const closedAt = Number(localStorage.getItem(STORAGE_KEY) || 0);
    if (Date.now() - closedAt < COOLDOWN_MS) return;

    const onInstallPrompt = (e) => {
      e.preventDefault();
      setInstallEvent(e);
    };
    window.addEventListener("beforeinstallprompt", onInstallPrompt);

    const timer = setTimeout(() => setVisible(true), SHOW_DELAY_MS);
    return () => {
      clearTimeout(timer);
      window.removeEventListener("beforeinstallprompt", onInstallPrompt);
    };
  }, []);

  const close = () => {
    localStorage.setItem(STORAGE_KEY, String(Date.now()));
    setVisible(false);
  };

  const install = async () => {
    if (!installEvent) return;
    installEvent.prompt();
    await installEvent.userChoice;
    setInstallEvent(null);
    close();
  };

  if (!visible) return null;

  return (
    <div className="fixed bottom-16 md:bottom-6 right-4 left-4 z-50 sm:left-auto sm:w-[380px] animate-fade-in-up">
      <div className="relative rounded-2xl border border-slate-800 bg-slate-950/90 p-5 shadow-2xl shadow-black/80 backdrop-blur-md">
        {/* Close Button */}
        <button
          onClick={close}
          aria-label="Yopish"
          className="absolute right-3.5 top-3.5 rounded-full p-1 text-slate-500 hover:bg-slate-900 hover:text-white transition-colors duration-200"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Brand Header */}
        <div className="mb-3 flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-green-600 shadow-md shadow-emerald-500/10">
            <img src="/logo.svg" alt="Logo" width={26} height={26} className="brightness-0 invert" />
          </div>
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400">Futbol Yangiliklari</h4>
            <p className="text-sm font-bold text-white leading-tight">Orqada qolib ketmang!</p>
          </div>
        </div>

        {/* Text */}
        <p className="mb-4 text-xs leading-relaxed text-slate-400">
          Eng so&apos;nggi jahon futboli xabarlari — tushunarli, qisqa va o&apos;zbek tilida. Obuna bo&apos;ling va birinchilardan bo&apos;lib bilib oling.
        </p>

        {/* Actions */}
        <div className="flex flex-col gap-2">
          <a
            href="https://t.me/futbolxabarida"
            target="_blank"
            rel="noopener noreferrer"
            onClick={close}
            className="flex items-center justify-center gap-2 rounded-xl bg-sky-500 px-4 py-2.5 text-xs font-bold text-white hover:bg-sky-400 hover:scale-[1.01] active:scale-[0.99] transition-all duration-200"
          >
            📢 Telegram kanalga a&apos;zo bo&apos;lish
          </a>
          
          {installEvent && (
            <button
              onClick={install}
              className="flex items-center justify-center gap-2 rounded-xl border border-slate-800 bg-slate-900/40 px-4 py-2.5 text-xs font-semibold text-slate-300 hover:border-emerald-500/30 hover:text-white hover:bg-slate-900 transition-all duration-200"
            >
              📲 Ilovani o&apos;rnatish (PWA)
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
