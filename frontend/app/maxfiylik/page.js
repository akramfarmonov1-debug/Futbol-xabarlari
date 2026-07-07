export const metadata = {
  title: "Maxfiylik siyosati",
  description:
    "Futbol Xabar saytining maxfiylik siyosati: qanday ma'lumotlar to'planishi, cookie va mahalliy xotira ishlatilishi haqida.",
  alternates: { canonical: "/maxfiylik" },
};

export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl py-10">
      <h1 className="mb-2 text-3xl font-bold">Maxfiylik siyosati</h1>
      <p className="mb-8 text-sm text-slate-500">Oxirgi yangilanish: 2026-yil 7-iyul</p>

      <div className="space-y-5 leading-relaxed text-slate-300">
        <h2 className="text-xl font-bold text-white">Qanday ma&apos;lumot to&apos;playmiz</h2>
        <p>
          Futbol Xabar saytidan foydalanish uchun ro&apos;yxatdan o&apos;tish talab qilinmaydi va
          biz sizdan shaxsiy ma&apos;lumot so&apos;ramaymiz. Saytga tashrif davomida quyidagi
          texnik vositalar ishlatiladi:
        </p>
        <ul className="list-disc space-y-2 pl-6">
          <li>
            <strong className="text-white">Mahalliy xotira (localStorage)</strong> — obuna
            taklifi oynasini yopganingizni eslab qolish uchun. Bu ma&apos;lumot faqat sizning
            qurilmangizda saqlanadi va bizga yuborilmaydi.
          </li>
          <li>
            <strong className="text-white">Service worker keshi</strong> — sahifalarni
            tezroq ochish va internetsiz rejimda ko&apos;rsatish uchun. Bu ham faqat
            qurilmangizda ishlaydi.
          </li>
        </ul>

        <h2 className="pt-2 text-xl font-bold text-white">Reklama va statistika</h2>
        <p>
          Saytda reklama bloklari joylashtirilishi mumkin. Reklama tarmoqlari (masalan,
          Google AdSense) o&apos;z cookie&apos;laridan foydalanishi mumkin — bunday holatda
          ular o&apos;z maxfiylik siyosatlariga bo&apos;ysunadi. Tashrif statistikasi
          yig&apos;ilsa, u faqat umumlashtirilgan (anonim) ko&apos;rinishda tahlil qilinadi.
        </p>

        <h2 className="pt-2 text-xl font-bold text-white">Uchinchi tomon havolalari</h2>
        <p>
          Maqolalarimizda asl manbalarga va Telegram xizmatlariga havolalar mavjud. Ushbu
          saytlarga o&apos;tganingizda ularning maxfiylik qoidalari amal qiladi.
        </p>

        <h2 className="pt-2 text-xl font-bold text-white">Murojaat</h2>
        <p>
          Maxfiylik bo&apos;yicha savollaringiz bo&apos;lsa,{" "}
          <a href="/aloqa" className="text-sky-400 hover:underline">
            Aloqa sahifasi
          </a>{" "}
          orqali yozing.
        </p>
      </div>
    </div>
  );
}
