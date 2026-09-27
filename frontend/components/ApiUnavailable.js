// apiGet null qaytarganda (backend javob bermadi) ko'rsatiladi. "Hozircha
// yangilik yo'q" bilan adashtirmaslik uchun alohida: o'quvchi sayt tashlab
// qo'yilgan deb o'ylamasin, admin esa nosozlikni bir qarashda ko'rsin.
export default function ApiUnavailable() {
  return (
    <div
      role="status"
      className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-10 text-center"
    >
      <p className="mb-2 text-sm font-bold text-amber-300">
        Server vaqtincha javob bermayapti
      </p>
      <p className="text-sm leading-relaxed text-slate-400">
        Bir necha daqiqadan so‘ng sahifani yangilang.
      </p>
    </div>
  );
}
