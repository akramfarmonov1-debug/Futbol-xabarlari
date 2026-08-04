# Futbol Xabar — Tuzatish rejasi

Ushbu reja NEXT_TASKS.md da belgilangan ustuvorliklar va loyiha tahlili asosida
tuzilgan. Har bir band aniq, mustaqil bajariladigan bosqich sifatida berilgan.

---

## 1. Dublikat xabarlar filtrini mustahkamlash (backend — eng muhim)

**Maqsad:** Bir voqeani boshqa manbadan olganda yangi maqola yaratilmasligi,
ammo haqiqiy yangi rivojlanish bloklanmasligi.

1. [`event_dedup.py`](../backend/app/services/event_dedup.py)
   - Yangi `EventMatch` baholashda **stored `event_key`** (ArticleQuality) ni
     asosiy signal sifatida ishlatish: yangi xabarning `analyze_news` dan kelgan
     `event_key` va `entities` to'plamini mavjud maqolalar `event_key` /
     `entities` bilan taqqoslash.
   - `find_duplicate_article()` ga `event_key`, `entities` parametrlarini qo'shish
     va `ArticleQuality` bilan `join` orqali nomzodlarni olish.
   - Jaccard + `SequenceMatcher` zamonaviy usulga: token almashtirish + nom
     lug'ati + `event_key` prefiks mosligi. "Real yangi rivojlanish" ni aniqlash
     uchun `source_published_at` yaqinligi va `fact` yangiligi signali qo'shish.
2. [`pipeline.py`](../backend/app/pipeline.py)
   - Dublikat tekshiruviga `analysis["event_key"]` va `analysis["entities"]` ni
     uzatish (raw bosqichdan tashqari AI tahlilidan keyingi bosqichda).
3. [`ingestion_log.py`](../backend/app/services/ingestion_log.py)
   - Yangi `decision` qiymatlari: `duplicate_event` (mavjud) + `update_followup`
     (yangilanish sifatida qabul qilingan) log'ini qo'shish.
4. **Testlar** ([`test_event_dedup.py`](../backend/tests/test_event_dedup.py)):
   - Bir voqea — ikki manba → dublikat.
   - O'xshash sarlavha, boshqa voqea → dublikat emas.
   - "FIFA investitsiyasi" / "diskriminatsiya" takroriy maqolalari → bloklanadi.
   - Natija yangilangan davomiy xabar → `update_followup`, bloklanmaydi.

**Qabul mezoni:** Bosh sahifada bir voqea bo'yicha bitta asosiy maqola; boshqa
manbadan olingan bir xil xabar yangi maqola yaratmaydi; yangi faktli davomiy
xabar o'tkazib yuborilmaydi.

---

## 2. O'zbekcha tahrir sifatini kuchaytirish (backend)

1. **Nomlar lug'ati** — yangi modul
   [`names_glossary.py`](../backend/app/services/names_glossary.py):
   - Klub/futbolchi/turnir nomlarining kanonik o'zbekcha yozilishi uchun
     lug'at (`Chelsea → Chelsi`, `Wrexham → Vrekshem`, `Rangers → Reynjers` va h.k.).
   - `normalize_analysis()` va yangi `normalize_uz_text()` bilan integratsiya.
2. [`ai_agent.py`](../backend/app/services/ai_agent.py) — `SYSTEM_PROMPT` ga
   qat'iy tabiiy/journalistik o'zbek tili talablari:
   - sarlavha 70–90 belgidan oshmasligi,
   - clickbait / sun'iy iboralar / ortiqcha takrorlarni taqiqlash,
   - tarjima emas, o'zbek jurnalisti uslubi.
3. [`content_quality.py`](../backend/app/services/content_quality.py)
   - `TEXT_REPLACEMENTS` ni nomlar lug'ati bilan kengaytirish.
   - Uzun sarlavha, takroriy so'zlar va zid jumlalar uchun avtomatik tekshiruv
     (`analysis_is_publishable` ga qo'shimcha qoidalar).
   - Sifatsiz matnni aniqlaganda qayta generatsiya yoki hech bo'lmaganda
     `reasons` ga belgi qo'shish (pipeline davomida).
4. **Testlar** — imlo/transliteratsiya xatolari va sarlavha uzunligi uchun.

**Qabul mezoni:** Sarlavha odatda 70–90 belgidan oshmaydi; yangi maqolalarda
imlo/transliteratsiya xatolari yo'q; matn tarjima kabi emas, o'zbek jurnalisti
yozgandek o'qiladi.

---

## 3. Planshet navigatsiyasini tuzatish (frontend)

1. [`Header.js`](../frontend/components/Header.js)
   - Kategoriya menyusini konteyner ichida gorizontal scroll qilinadigan qilib
     tuzatish: `overflow-x-auto` + `scrollbar-width: none`, `scroll-snap-type`,
     sahiyani kengaytirmaslik uchun `min-w-0` va `flex-nowrap`.
   - `body`/`html` da `overflow-x: hidden` (faqat kerakli hollarda) — asosan
     menyuning o'zi scroll bo'lishi kerak.
2. **Tekshirish** — 390, 640, 678, 768, 1024, 1440 px kengliklarda
   `documentElement.scrollWidth === documentElement.clientWidth` sharti.
3. **Qabul mezoni:** Barcha kengliklarda sahifa gorizontal scroll chiqarmaydi,
   barcha kategoriyalarga kirish mumkin, sticky header va pastki mobil nav bir-
   biriga xalaqit bermaydi.

---

## 4. Maqola sahifasini boyitish (frontend + backend)

1. **O'xshash xabarlar** — backend [`news.py`](../backend/app/routers/news.py) ga
   `GET /api/news/{slug}/related` endpoint (kategoriya + umumiy teglar + vaqt
   oynasi, 3–5 ta) qo'shish; [`maqola/[slug]/page.js`](../frontend/app/maqola/[slug]/page.js)
   da ko'rsatish.
2. **"Oxirgi yangilangan" sanasi** — `published_at` dan tashqari
   `updated_at`/`last_modified` maydonini model va API'ga qo'shish (kerak bo'lsa)
   yoki mavjud `published_at`/`created_at` dan foydalanish; sahifada ko'rsatish.
3. **Mualliflik** — "Futbol Xabar tahririyati" muallif yorlig'ini sahifada
   ko'rsatish (JSON-LD author'da mavjud, UI ga qo'shish).
4. **Tuzatish siyosati sahifasi** — yangi [`maxfiylik`](../frontend/app/maxfiylik/page.js)
   kabi statik sahifa `/tahrir-siyosati` (yoki `/tuzatishlar`).
5. **Havolani nusxalash** — Telegram'dan tashqari "Havolani nusxalash" tugmasi
   (client component, `navigator.clipboard`).
6. **Qabul mezoni:** Har bir maqolada 3–5 ta o'xshash xabar, oxirgi yangilangan
   sana, mualliflik va nusxalash tugmasi mavjud.

---

## 5. Reklama bloklarini production holatiga keltirish (frontend)

1. [`AdPlaceholder.js`](../frontend/components/AdPlaceholder.js)
   - Reklama provayderi ulangan bo'lsagina ko'rsatish
     (`NEXT_PUBLIC_ADSENSE_CLIENT_ID` mavjudligi yoki env flag).
   - Provayder bo'lmasa placeholder'ni yashirish; yoqilganda joy oldindan
     band qilinishi uchun `min-height` saqlash (CLS oldini olish).
   - Mobil/desktop o'lchamlarini alohida: mobil `320x50`, desktop `728x90` /
     `300x250`.
2. **Qabul mezoni:** Provayder ulannagan paytda foydalanuvchiga placeholder
   ko'rinmaydi; reklama yoqilganda layout siljishi kuzatilmaydi.

---

## 6. SEO va tezlikni yakuniy tasdiqlash (frontend/backend — operatsion)

1. [`sitemap.js`](../frontend/app/sitemap.js) va
   [`news-sitemap.xml`](../frontend/app/news-sitemap.xml/route.js) ni
   `https://www.futbolxabar.uz` canonical bilan tekshirish.
2. `www` domeni canonical ekanini `robots.txt` va sitemap da tasdiqlash.
3. Core Web Vitals (LCP, CLS, INP) va `NewsArticle` rich result testi.
4. 404 / 5xx / canonical xatolar monitoringi.

**Qabul mezoni:** Google Search Console'da `sitemap.xml` qabul qilingan,
`NewsArticle` sxemasi xatosiz, muhim sahifalar indekslangan.

---

## Bajarish tartibi (tavsiya)

1. Dublikat filtri (backend + testlar)
2. O'zbekcha tahrir (nomlar lug'ati + prompt + validator)
3. Planshet menyusi (frontend)
4. Maqola sahifasi boyitish (backend endpoint + frontend UI)
5. Reklama bloklari (frontend)
6. Avtomatik testlar + lokal build
7. Commit + GitHub push
8. Vercel/Render deploy va jonli audit
