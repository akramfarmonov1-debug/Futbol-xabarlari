"use client";

import { useState, useEffect } from "react";
import { API_URL } from "../lib/api";

const REACTION_CONFIG = [
  { key: "fire", emoji: "🔥", label: "Olov" },
  { key: "like", emoji: "⚽", label: "Zo‘r" },
  { key: "applause", emoji: "👏", label: "Qoyil" },
  { key: "shock", emoji: "😮", label: "Hayrat" },
];

export default function ArticleReactions({ slug, initialReactions = {} }) {
  const [reactions, setReactions] = useState(() => ({
    fire: 0,
    like: 0,
    applause: 0,
    shock: 0,
    ...(initialReactions || {}),
  }));
  const [userVoted, setUserVoted] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(`futbolxabar_reactions_${slug}`);
      if (stored) {
        setUserVoted(JSON.parse(stored));
      }
    } catch {
      // localStorage xatosi e'tiborsiz qoldiriladi
    }
  }, [slug]);

  const handleReact = async (key) => {
    if (userVoted[key] || isSubmitting) return;

    // Optimistik yangilash
    const updatedUserVoted = { ...userVoted, [key]: true };
    setUserVoted(updatedUserVoted);
    setReactions((prev) => ({
      ...prev,
      [key]: (prev[key] || 0) + 1,
    }));

    try {
      localStorage.setItem(
        `futbolxabar_reactions_${slug}`,
        JSON.stringify(updatedUserVoted),
      );
    } catch {
      // pass
    }

    setIsSubmitting(true);
    try {
      const res = await fetch(
        `${API_URL}/api/news/${encodeURIComponent(slug)}/react?reaction=${key}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        },
      );
      if (res.ok) {
        const latest = await res.json();
        setReactions((prev) => ({ ...prev, ...latest }));
      }
    } catch {
      // Backend uzilgan bo'lsa optimistik qiymat qoladi
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-900 bg-slate-950/40 p-5 backdrop-blur-sm">
      <div className="mb-3.5 flex items-center justify-between">
        <h3 className="text-xs font-extrabold uppercase tracking-widest text-slate-300">
          Ushbu xabarga munosabatingiz:
        </h3>
        <span className="text-[11px] text-slate-500 font-medium">
          Ovoz berish uchun bosing
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-2.5">
        {REACTION_CONFIG.map(({ key, emoji, label }) => {
          const count = reactions[key] || 0;
          const isSelected = !!userVoted[key];

          return (
            <button
              key={key}
              type="button"
              disabled={isSelected}
              onClick={() => handleReact(key)}
              title={label}
              className={`group inline-flex items-center gap-2 rounded-xl border px-3.5 py-2 text-xs font-semibold transition-all duration-200 active:scale-95 ${
                isSelected
                  ? "border-emerald-500/40 bg-emerald-500/15 text-emerald-300 cursor-default"
                  : "border-slate-800 bg-slate-900/60 text-slate-300 hover:border-slate-700 hover:bg-slate-900 cursor-pointer"
              }`}
            >
              <span className="text-base leading-none transition-transform group-hover:scale-125">
                {emoji}
              </span>
              <span className="font-bold text-slate-200">{count}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
