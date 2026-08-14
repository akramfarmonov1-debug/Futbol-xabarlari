"use client";

import { useEffect, useState } from "react";
import { getNotificationPermission, isPushSupported, subscribeToPushNotifications } from "../lib/push";

export default function NotificationBell() {
  const [supported, setSupported] = useState(false);
  const [permission, setPermission] = useState("default");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    isPushSupported().then((sup) => {
      setSupported(sup);
      if (sup) {
        setPermission(getNotificationPermission());
      }
    });
  }, []);

  if (!supported) return null;

  const handleToggle = async () => {
    if (permission === "granted") {
      setMessage("✅ Bildirishnomalar faol!");
      setTimeout(() => setMessage(""), 3000);
      return;
    }

    setLoading(true);
    try {
      await subscribeToPushNotifications();
      setPermission("granted");
      setMessage("🔔 Bildirishnomalar muvaffaqiyatli yoqildi!");
      setTimeout(() => setMessage(""), 4000);
    } catch (err) {
      setMessage(err.message || "Xatolik yuz berdi");
      setTimeout(() => setMessage(""), 4000);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex items-center">
      <button
        onClick={handleToggle}
        disabled={loading}
        title={permission === "granted" ? "Bildirishnomalar yoqilgan" : "Tezkor yangiliklarga obuna bo'lish"}
        className={`relative flex h-8 w-8 items-center justify-center rounded-full border transition-all duration-200 ${
          permission === "granted"
            ? "border-emerald-500/40 bg-emerald-950/40 text-emerald-400 hover:bg-emerald-900/40"
            : "border-slate-800 bg-slate-900/60 text-slate-400 hover:border-amber-500/40 hover:text-amber-400 hover:bg-slate-900"
        }`}
      >
        <span className="text-sm">{loading ? "⏳" : permission === "granted" ? "🔔" : "🔕"}</span>
        {permission !== "granted" && (
          <span className="absolute -top-0.5 -right-0.5 flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
          </span>
        )}
      </button>

      {message && (
        <div className="absolute top-10 right-0 z-50 whitespace-nowrap rounded-xl border border-slate-800 bg-slate-950/95 px-3 py-1.5 text-[11px] font-semibold text-slate-200 shadow-xl backdrop-blur-md animate-fade-in-up">
          {message}
        </div>
      )}
    </div>
  );
}
