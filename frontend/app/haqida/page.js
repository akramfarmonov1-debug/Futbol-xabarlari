export const metadata = {
  title: "Biz haqimizda",
  description:
    "Futbol Xabar — jahon futboli yangiliklarini o'zbek tilida yetkazuvchi platforma. Kontent qanday tayyorlanishi va tahririyat tamoyillari haqida.",
  alternates: { canonical: "/haqida" },
};

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl py-10">
      <h1 className="mb-6 text-3xl font-bold">Biz haqimizda</h1>

      <div className="space-y-5 leading-relaxed text-slate-300">
        <p>
          <strong className="text-white">Futbol Xabar</strong> (futbolxabar.uz) — dunyodagi eng muhim
          jahon futboli yangiliklarini o&apos;zbek tilida, qisqa va tushunarli shaklda
          yetkazib beruvchi yangiliklar platformasi. Maqsadimiz — O&apos;zbekistondagi
          futbol muxlislarini jahon futbolidagi eng
          so&apos;nggi voqealardan xabardor qilib borish.
        </p>

        <h2 className="pt-2 text-xl font-bold text-white">Kontent qanday tayyorlanadi</h2>
        <p>
          Biz BBC Sport, The Guardian, Sky Sports, ESPN kabi jahonning eng nufuzli sport
          nashrlarining ochiq RSS manbalarini kuzatib boramiz. Har bir yangilik sun&apos;iy intellekt yordamida o&apos;zbek tiliga
          moslashtiriladi: sarlavha, qisqa xulosa, to&apos;liq bayon va &quot;bu nima
          degani?&quot; amaliy izohi tayyorlanadi.
        </p>
        <p>
          Halollik — asosiy tamoyilimiz: har bir maqola tagida <strong className="text-white">asl
          manbaga havola</strong> ko&apos;rsatiladi, muhimlik bahosi (1–5 yulduz) esa
          yangilikning soha uchun ahamiyatini bildiradi. Maqolalar saytga chiqishidan oldin
          tahririy nazoratdan o&apos;tadi.
        </p>

        <h2 className="pt-2 text-xl font-bold text-white">Nima uchun bepul</h2>
        <p>
          Futbol Xabar — ochiq platforma. Kontentimiz hammaga bepul, sayt reklama va homiylik
          hisobidan rivojlantiriladi. Yangiliklardan birinchilardan bo&apos;lib xabar topish
          uchun{" "}
          <a
            href="https://t.me/futbolxabarida"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sky-400 hover:underline"
          >
            Telegram kanalimizga
          </a>{" "}
          obuna bo&apos;ling.
        </p>

        <h2 className="pt-2 text-xl font-bold text-white">Bog&apos;lanish</h2>
        <p>
          Takliflar, xatolar haqida xabar yoki hamkorlik bo&apos;yicha{" "}
          <a href="/aloqa" className="text-sky-400 hover:underline">
            Aloqa sahifasi
          </a>{" "}
          orqali murojaat qiling.
        </p>
      </div>
    </div>
  );
}
