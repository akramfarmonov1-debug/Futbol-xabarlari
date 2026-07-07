"use client";

export default function AdPlaceholder({ type = "sidebar" }) {
  // Bosh sahifa yon paneli uchun kvadrat/minor banner, maqola osti uchun gorizontal banner
  const dimensions = type === "sidebar" ? "h-60" : "h-24 sm:h-28";
  const label = type === "sidebar" ? "300x250 Reklama" : "728x90 Reklama";

  return (
    <div className="w-full">
      <div
        className={`flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-800 bg-slate-900/40 p-4 text-center transition-colors hover:border-green-500/30 ${dimensions}`}
      >
        <span className="text-xs uppercase tracking-widest text-slate-600">Reklama</span>
        <span className="mt-1 text-xs text-slate-500">{label}</span>
        <span className="mt-2 text-[10px] text-slate-600">reklama@futbolxabar.uz</span>
      </div>
    </div>
  );
}
