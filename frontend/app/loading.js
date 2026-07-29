export default function Loading() {
  return (
    <div className="space-y-6 py-6" role="status" aria-label="Yuklanmoqda">
      <div className="h-64 animate-pulse rounded-3xl border border-slate-900 bg-slate-950/60" />
      <div className="grid gap-6 sm:grid-cols-2">
        {[0, 1, 2, 3].map((item) => (
          <div
            key={item}
            className="h-72 animate-pulse rounded-2xl border border-slate-900 bg-slate-950/40"
          />
        ))}
      </div>
      <span className="sr-only">Sahifa yuklanmoqda…</span>
    </div>
  );
}
