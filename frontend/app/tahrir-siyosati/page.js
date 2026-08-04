export const metadata = {
  title: "Tahrir va xatolarni tuzatish siyosati",
  description:
    "Futbol Xabar tahririyatining tahrir qoidalari, xato aniqlanganda tuzatish tartibi va o'quvchi murojaatlari haqida ma'lumot.",
  alternates: { canonical: "/tahrir-siyosati" },
};

export default function EditorialPolicyPage() {
  return (
    <div className="mx-auto max-w-3xl py-10">
      <h1 className="mb-2 text-3xl font-bold">Tahrir va xatolarni tuzatish siyosati</h1>
      <p className="mb-8 text-sm text-slate-500">Oxirgi yangilanish: 2026-yil iyul</p>

      <div className="space-y-5 leading-relaxed text-slate-300">
        <h2 className="text-xl font-bold text-white">Tahririyat tamoyillari</h2>
        <p>
          Futbol Xabar tahririyati jahon futbolining muhim yangiliklarini ishonchli
          manbalardan yig'ib, o'zbek tilida yetkazadi. Barcha maqolalar nashrdan
          oldin fakt tekshiruvi va sifat nazoratidan o'tadi. Maqsadimiz — aniq,
          xolis va tushunarli sport jurnalistikasi.
        </p>

        <h2 className="pt-2 text-xl font-bold text-white">Xato aniqlanganida</h2>
        <p>
          Agar maqolada faktik xato, noto'g'ri sana, hisob yoki ism-sharif
          yozilishini sezsangiz, iltimos bizga xabar bering. Har bir murojaat
          tekshiriladi:
        </p>
        <ul className="list-disc space-y-2 pl-6">
          <li>Xato tasdiqlansa, maqola iloji boricha tezroq tuzatiladi.</li>
          <li>
            Muhim tuzatishlar maqola ichida belgilanadi va "Oxirgi yangilangan"
            sanasi yangilanadi.
          </li>
          <li>
            Manba yangiligining o'zida xatolik bo'lsa, maqolaga asl manba
            havolasi orqali o'quvchi uni mustaqil tekshirishi mumkin.
          </li>
        </ul>

        <h2 className="pt-2 text-xl font-bold text-white">AI yordamida tayyorlangan kontent</h2>
        <p>
          Maqolalar AI yordamida o'zbek tiliga moslashtiriladi va tahririyat
          tomonidan tekshiriladi. AI vositasidan tarjima va tahlil uchun foydalanamiz,
          lekin yakuniy javobgarlik tahririyat zimmasida.
        </p>

        <h2 className="pt-2 text-xl font-bold text-white">Manbalar va dublikatlar</h2>
        <p>
          Bitta voqea bir nechta manbada yoritilganda, eng to'liq va ishonchli manba
          asos qilib olinadi. Qolgan manbalar maqolaning "Asl manba" qismida ko'rsatiladi.
          Bir voqeani takroran chop etmaslik uchun avtomatik dublikat filtri ishlaydi.
        </p>

        <h2 className="pt-2 text-xl font-bold text-white">Murojaat qilish</h2>
        <p>
          Xato yoki tahrir bo'yicha murojaatlar uchun{" "}
          <a href="/aloqa" className="text-sky-400 hover:underline">
            Aloqa sahifasi
          </a>{" "}
          orqali yozing. Har bir murojaat ko'rib chiqiladi.
        </p>
      </div>
    </div>
  );
}
