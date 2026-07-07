"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "futbolxabar_popup_closed_at";
const SHOW_DELAY_MS = 10_000; // 10 soniyadan keyin chiqadi
const COOLDOWN_MS = 3 * 24 * 60 * 60 * 1000; // yopilgach 3 kun ko'rinmaydi

export default function SubscribePopup() {
  const [visible, setVisible] = useState(false);
  const [installEvent, setInstallEvent] = useState(null);

  useEffect(() => {
    // PWA sifatida ochilgan bo'lsa popup kerak emas
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
    <div className="fixed bottom-4 right-4 left-4 z-50 sm:left-auto sm:w-96">
      <div className="relative rounded-2xl border border-slate-700 bg-slate-900 p-5 shadow-2xl shadow-black/50">
        <button
          onClick={close}
          aria-label="Yopish"
          className="absolute right-3 top-3 rounded-full px-2 py-0.5 text-slate-500 hover:bg-slate-800 hover:text-white"
        >
          ✕
        </button>

        <div className="mb-2 flex items-center gap-2">
          <img src="/logo.svg" alt="Futbol Xabar" width={36} height={36} />
          <p className="font-bold">futbol yangiliklaridan orqada qolmang!</p>
        </div>
        <p className="mb-4 text-sm text-slate-400">
          Eng muhim jahon futboli yangiliklari — har kuni, o&apos;zbek
          tilida. Telegram kanalimizga obuna bo&apos;ling.
        </p>

        <div className="flex flex-wrap gap-2">
          <a
            href="https://t.me/futbolxabarlari"
            target="_blank"
            rel="noopener noreferrer"
            onClick={close}
            className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-400"
          >
            📢 Kanalga obuna bo&apos;lish
          </a>
          {installEvent && (
            <button
              onClick={install}
              className="rounded-lg border border-slate-600 px-4 py-2 text-sm text-slate-200 hover:border-green-500 hover:text-white"
            >
              📲 Ilovani o&apos;rnatish
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
