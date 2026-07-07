"use client";

import { useCallback, useEffect, useState } from "react";
import { API_URL } from "../../lib/api";

const STATUSES = [
  { value: "pending", label: "⏳ Kutilmoqda" },
  { value: "published", label: "✅ Chop etilgan" },
  { value: "rejected", label: "❌ Rad etilgan" },
];

export default function AdminPage() {
  const [token, setToken] = useState("");
  const [loggedIn, setLoggedIn] = useState(false);
  const [status, setStatus] = useState("pending");
  const [articles, setArticles] = useState([]);
  const [stats, setStats] = useState(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const saved = localStorage.getItem("admin_token");
    if (saved) {
      setToken(saved);
      setLoggedIn(true);
    }
  }, []);

  const api = useCallback(
    async (path, options = {}) => {
      const res = await fetch(`${API_URL}${path}`, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          "X-Admin-Token": token,
          ...(options.headers || {}),
        },
      });
      if (res.status === 401) {
        setLoggedIn(false);
        localStorage.removeItem("admin_token");
        throw new Error("Token noto'g'ri");
      }
      if (!res.ok) throw new Error((await res.json()).detail || "Xatolik");
      return res.json();
    },
    [token],
  );

  const load = useCallback(async () => {
    try {
      const [list, statistics] = await Promise.all([
        api(`/api/admin/articles?status=${status}`),
        api("/api/admin/stats"),
      ]);
      setArticles(list);
      setStats(statistics);
    } catch (error) {
      setMessage(error.message);
    }
  }, [api, status]);

  useEffect(() => {
    if (loggedIn) load();
  }, [loggedIn, load]);

  async function action(path, method = "POST") {
    try {
      await api(path, { method });
      setMessage("✅ Bajarildi");
      load();
    } catch (error) {
      setMessage(`❌ ${error.message}`);
    }
  }

  if (!loggedIn) {
    return (
      <div className="mx-auto max-w-sm py-24">
        <h1 className="mb-4 text-xl font-bold">🔐 Admin panel</h1>
        <input
          type="password"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder="Admin token"
          className="mb-3 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 outline-none focus:border-green-500"
        />
        <button
          onClick={() => {
            localStorage.setItem("admin_token", token);
            setLoggedIn(true);
          }}
          className="w-full rounded-lg bg-green-600 py-2 font-semibold hover:bg-green-500"
        >
          Kirish
        </button>
      </div>
    );
  }

  return (
    <div className="py-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">🛠 Admin panel</h1>
        <button
          onClick={() => {
            localStorage.removeItem("admin_token");
            setLoggedIn(false);
          }}
          className="text-sm text-slate-400 hover:text-white"
        >
          Chiqish
        </button>
      </div>

      {stats && (
        <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-5">
          {[
            ["Jami", stats.jami],
            ["Kutilmoqda", stats.kutilmoqda],
            ["Chop etilgan", stats.chop_etilgan],
            ["Rad etilgan", stats.rad_etilgan],
            ["Telegramda", stats.telegramga_yuborilgan],
          ].map(([label, value]) => (
            <div key={label} className="rounded-xl border border-slate-800 p-4 text-center">
              <div className="text-2xl font-bold text-green-400">{value}</div>
              <div className="text-xs text-slate-400">{label}</div>
            </div>
          ))}
        </div>
      )}

      <div className="mb-4 flex gap-2">
        {STATUSES.map((s) => (
          <button
            key={s.value}
            onClick={() => setStatus(s.value)}
            className={`rounded-full px-4 py-1.5 text-sm ${
              status === s.value
                ? "bg-green-600 text-white"
                : "border border-slate-700 text-slate-300"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {message && <div className="mb-4 text-sm text-slate-300">{message}</div>}

      <div className="space-y-4">
        {articles.length === 0 && (
          <p className="py-10 text-center text-slate-500">Bu holatda maqolalar yo&apos;q.</p>
        )}
        {articles.map((article) => (
          <div key={article.id} className="rounded-xl border border-slate-800 p-5">
            <div className="mb-1 flex flex-wrap items-center gap-2 text-xs text-slate-400">
              <span className="rounded-full bg-green-500/10 px-2 py-0.5 text-green-400">
                {article.category?.name || "—"}
              </span>
              <span>{"⭐".repeat(article.importance)}</span>
              <span>{article.source_name}</span>
              {article.sent_to_telegram && <span>📨 Telegramda</span>}
            </div>
            <h2 className="mb-1 font-semibold">{article.title}</h2>
            <p className="mb-3 text-sm text-slate-400">{article.summary}</p>
            <div className="flex flex-wrap gap-2 text-sm">
              {article.status !== "published" && (
                <button
                  onClick={() => action(`/api/admin/articles/${article.id}/approve`)}
                  className="rounded-lg bg-green-700 px-3 py-1.5 hover:bg-green-600"
                >
                  ✅ Tasdiqlash
                </button>
              )}
              {article.status === "published" && !article.sent_to_telegram && (
                <button
                  onClick={() => action(`/api/admin/articles/${article.id}/telegram`)}
                  className="rounded-lg bg-sky-700 px-3 py-1.5 hover:bg-sky-600"
                >
                  📤 Telegramga
                </button>
              )}
              {article.status === "pending" && (
                <button
                  onClick={() => action(`/api/admin/articles/${article.id}/reject`)}
                  className="rounded-lg bg-yellow-800 px-3 py-1.5 hover:bg-yellow-700"
                >
                  🚫 Rad etish
                </button>
              )}
              <button
                onClick={() => action(`/api/admin/articles/${article.id}`, "DELETE")}
                className="rounded-lg bg-red-900 px-3 py-1.5 hover:bg-red-800"
              >
                🗑 O&apos;chirish
              </button>
              <a
                href={article.original_url}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-lg border border-slate-700 px-3 py-1.5 text-slate-300"
              >
                🔗 Manba
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
