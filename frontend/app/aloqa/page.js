export const metadata = {
  title: "Aloqa",
  description:
    "Futbol Xabar tahririyati bilan bog'lanish: takliflar, xatolar haqida xabar berish va hamkorlik bo'yicha murojaatlar.",
  alternates: { canonical: "/aloqa" },
};

const CONTACTS = [
  {
    icon: "📢",
    title: "Telegram kanal",
    value: "@futbolxabarida",
    href: "https://t.me/futbolxabarida",
    note: "Yangiliklar va e'lonlar",
  },
  {
    icon: "🤖",
    title: "Telegram bot",
    value: "@Futbolxabari_bot",
    href: "https://t.me/Futbolxabari_bot",
    note: "Yangiliklarni botda o'qish",
  },
  {
    icon: "✉️",
    title: "Elektron pochta",
    value: "rovshanovazizbek0@gmail.com",
    href: "mailto:rovshanovazizbek0@gmail.com",
    note: "Hamkorlik va reklama bo'yicha",
  },
];

export default function ContactPage() {
  return (
    <div className="mx-auto max-w-3xl py-10">
      <h1 className="mb-3 text-3xl font-bold">Aloqa</h1>
      <p className="mb-8 leading-relaxed text-slate-300">
        Taklifingiz bormi, maqolada xatolik topdingizmi yoki hamkorlik qilmoqchimisiz?
        Quyidagi kanallar orqali murojaat qiling — odatda 1-2 ish kuni ichida javob beramiz.
      </p>

      <div className="grid gap-4 sm:grid-cols-2">
        {CONTACTS.map((c) => (
          <a
            key={c.title}
            href={c.href}
            target={c.href.startsWith("http") ? "_blank" : undefined}
            rel={c.href.startsWith("http") ? "noopener noreferrer" : undefined}
            className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 transition-colors hover:border-green-500"
          >
            <div className="mb-2 text-2xl">{c.icon}</div>
            <div className="font-bold text-white">{c.title}</div>
            <div className="text-sky-400">{c.value}</div>
            <div className="mt-1 text-sm text-slate-500">{c.note}</div>
          </a>
        ))}
      </div>

      <div className="mt-8 rounded-xl border border-green-900 bg-green-500/5 p-5 text-sm leading-relaxed text-slate-300">
        <strong className="text-green-400">Xatolik topdingizmi?</strong> Maqoladagi noaniqlik
        yoki tarjima xatosi haqida yozsangiz, tekshirib tuzatamiz — bu platformani hamma
        uchun yaxshiroq qiladi.
      </div>
    </div>
  );
}
