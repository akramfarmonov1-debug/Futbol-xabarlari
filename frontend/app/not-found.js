import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-xl py-24 text-center">
      <div className="mb-5 text-5xl" aria-hidden="true">
        ⚽
      </div>
      <p className="mb-2 text-xs font-black uppercase tracking-[0.25em] text-emerald-400">
        404 · Sahifa topilmadi
      </p>
      <h1 className="mb-4 text-3xl font-black text-white">
        Bu sahifa maydonni tark etgan
      </h1>
      <p className="mb-7 text-sm leading-relaxed text-slate-400">
        Havola eskirgan yoki sahifa boshqa manzilga ko‘chirilgan bo‘lishi
        mumkin.
      </p>
      <Link
        href="/"
        className="inline-flex rounded-full bg-emerald-500 px-6 py-3 text-sm font-bold text-slate-950 transition hover:bg-emerald-400"
      >
        Bosh sahifaga qaytish
      </Link>
    </div>
  );
}
