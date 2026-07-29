"use client";

export default function ErrorPage({ reset }) {
  return (
    <div className="mx-auto max-w-xl py-24 text-center">
      <div className="mb-5 text-5xl" aria-hidden="true">
        🟨
      </div>
      <h1 className="mb-3 text-3xl font-black text-white">
        Vaqtinchalik xatolik yuz berdi
      </h1>
      <p className="mb-7 text-sm leading-relaxed text-slate-400">
        Ma’lumotni yuklashda uzilish bo‘ldi. Bir necha soniyadan keyin qayta
        urinib ko‘ring.
      </p>
      <button
        type="button"
        onClick={reset}
        className="rounded-full bg-emerald-500 px-6 py-3 text-sm font-bold text-slate-950 transition hover:bg-emerald-400"
      >
        Qayta urinish
      </button>
    </div>
  );
}
