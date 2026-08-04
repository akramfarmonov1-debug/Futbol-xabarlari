# Futbol Xabar — keyingi vazifalar

Oxirgi xolis baho: **8.8/10**  
Keyingi maqsad: **9.5+/10 darajadagi ishonchli va tahrirlangan futbol media mahsuloti**

## 1. Dublikat xabarlarni filtrlash — eng muhim

- [ ] AI maqola yaratishidan oldin yangi xabarni mavjud maqolalar bilan solishtirish.
- [ ] Sarlavha, asosiy shaxslar, klublar, turnir va voqea bo‘yicha o‘xshashlikni aniqlash.
- [ ] Bir voqea haqidagi bir nechta RSS xabaridan eng to‘liq va ishonchli manbani tanlash.
- [ ] Bir xil mazmundagi maqolani qayta chop etmaslik.
- [ ] Haqiqiy yangi rivojlanish bo‘lsa, uni dublikat emas, yangilanish sifatida qabul qilish.
- [ ] O‘tkazib yuborilgan xabar sababini logga yozish: `duplicate`, `low_quality`, `non_football` yoki `unsafe`.
- [ ] FIFA investitsiyasi va diskriminatsiya mavzulariga o‘xshash takroriy maqolalar bilan test qilish.

### Bajarilgan deb hisoblash mezoni

- Bir voqea bo‘yicha bosh sahifada faqat bitta asosiy maqola chiqadi.
- Pipeline bir xil xabarni boshqa manbadan olganda yangi maqola yaratmaydi.
- Yangi fakt yoki natijaga ega davomiy xabar bloklanmaydi.

## 2. O‘zbekcha tahrir sifatini kuchaytirish

- [ ] AI promptiga tabiiy, qisqa va jurnalistik o‘zbek tili talablarini qat’iy kiritish.
- [ ] Klub, futbolchi va turnir nomlari uchun yagona lug‘at yaratish.
- [ ] `muhokama/muxokama`, `Reynjers/Rangers`, `Vrekshem/Wrexham` kabi turli yozilishlarni birxillashtirish.
- [ ] Noqulay yoki mantiqan zid jumlalarni avtomatik tekshirish.
- [ ] Juda uzun sarlavhalarni maqola yaratilishidayoq qisqartirish.
- [ ] Sarlavha va matnda clickbait, sun’iy ibora hamda ortiqcha takrorlarni cheklash.
- [ ] Sifatsiz matnni chop etmasdan qayta generatsiya qilish.

### Bajarilgan deb hisoblash mezoni

- Sarlavha odatda 70–90 belgidan oshmaydi.
- Yangi maqolalarda aniqlangan imlo va transliteratsiya xatolari qolmaydi.
- Matn tarjima kabi emas, o‘zbek jurnalisti yozgandek o‘qiladi.

## 3. Planshet navigatsiyasini tuzatish

- [ ] 640–1024 px ekranlarda yuqori kategoriya menyusining sahifani yon tomonga kengaytirishini to‘xtatish.
- [ ] Menyuni konteyner ichida gorizontal aylantiriladigan qilish yoki elementlarni mos ravishda qisqartirish.
- [ ] Sahifaning o‘zida gorizontal scrollbar chiqmasligini ta’minlash.
- [ ] 390, 640, 678, 768, 1024 va 1440 px kengliklarda tekshirish.

### Bajarilgan deb hisoblash mezoni

- Har bir tekshirilgan kenglikda `documentElement.scrollWidth === documentElement.clientWidth`.
- Menyudagi barcha kategoriyalarga kirish mumkin.
- Pastki mobil navigatsiya va sticky header bir-biriga xalaqit bermaydi.

## 4. Maqola sahifasini boyitish

- [ ] Har bir maqolaga 3–5 ta o‘xshash xabar qo‘shish.
- [ ] “Oxirgi yangilangan” sanasini ko‘rsatish.
- [ ] Mas’ul muharrir yoki “Futbol Xabar tahririyati” muallifligini ko‘rsatish.
- [ ] Tahrir va xatolarni tuzatish siyosati sahifasini yaratish.
- [ ] Telegramdan tashqari havolani nusxalash tugmasini qo‘shish.

## 5. Reklama bloklarini production holatiga keltirish

- [ ] Reklama provayderi ulanmagan bo‘lsa, placeholder bloklarini foydalanuvchidan yashirish.
- [ ] Reklama yoqilganda layout siljishini oldini olish uchun joyni oldindan band qilish.
- [ ] Mobil va desktop reklama o‘lchamlarini alohida tekshirish.

## 6. SEO va tezlikni yakuniy tasdiqlash

- [ ] Google Search Console’ga `https://www.futbolxabar.uz/sitemap.xml` yuborish.
- [ ] `www` domeni asosiy property va canonical sifatida tanilganini tekshirish.
- [ ] Muhim sahifalarni URL Inspection orqali indeksatsiyaga yuborish.
- [ ] Mobil Core Web Vitals: LCP, CLS va INP natijalarini o‘lchash.
- [ ] Rich Results Test orqali `NewsArticle` sxemasini tekshirish.
- [ ] 404, 5xx, noto‘g‘ri canonical va indekslanmagan maqolalarni kuzatish.

## Ertangi bajarish tartibi

1. Dublikat filtri.
2. O‘zbekcha tahrir validatori va nomlar lug‘ati.
3. Planshet menyusi.
4. Avtomatik testlar va lokal build.
5. Alohida commit va GitHub’ga push.
6. Vercel/Render production deployini kuzatish.
7. Jonli saytni desktop, planshet va mobil o‘lchamlarda qayta audit qilish.

## Yakuniy qabul mezonlari

- [ ] Backend pipeline xatosiz ishlaydi.
- [ ] Bir voqea qayta-qayta chop etilmaydi.
- [ ] Yangi matnlarda sezilarli imlo va AI uslubidagi xatolar yo‘q.
- [ ] Barcha asosiy ekran kengliklarida gorizontal overflow yo‘q.
- [ ] Frontend production build muvaffaqiyatli.
- [ ] Jonli sayt, qidiruv, jadval, RSS va maqola sahifalari ishlaydi.
- [ ] Brauzer konsolida yangi xato yo‘q.

