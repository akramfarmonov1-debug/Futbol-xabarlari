# Futbol Xabar — Loyiha Tahlili

## 1. Umumiy tavsif

**Futbol Xabar** — jahon futbol yangiliklarini ishonchli RSS manbalaridan yig'ib, AI
yordamida o'zbek tiliga moslashtirib, sifat nazoratidan o'tkazib web sayt va
Telegram orqali yetkazuvchi avtomatlashtirilgan media platforma.

| Qism | Texnologiya | Manzil |
|---|---|---|
| Backend + REST API | FastAPI, SQLAlchemy 2.0, PostgreSQL/SQLite | `backend/` |
| AI Agent | Gemini API / Vertex AI / Claude — strukturali JSON | `backend/app/services/ai_agent.py` |
| Yangiliklar yig'uvchi | RSS 2.0 + Atom parser (stdlib xml.etree) | `backend/app/services/collector.py` |
| Frontend | Next.js 15, React 19, Tailwind CSS 4 | `frontend/` |
| Admin panel | Next.js sahifa + Admin API (X-Admin-Token) | `frontend/app/admin/` |
| Telegram bot | aiogram 3 | `bot/` |
| Deploy | Docker Compose (lokal), Render (prod) | `docker-compose.yml`, `render.yaml` |

## 2. Arxitektura va ish oqimi

```
┌─────────────────┐    ┌───────────────────────────────┐    ┌─────────────────┐
│  RSS manbalar   │ →  │  AI Agent pipeline             │ →  │  PostgreSQL /   │
│  BBC, Guardian, │    │  yig'ish → futbol filtri →     │    │  SQLite         │
│  Sky, ESPN,     │    │  dublikat filtri → AI tahlil → │    └────────┬────────┘
│  Sports.uz      │    │  kategoriya override → quality │             │
│                 │    │  gate → avto-nashr gate        │             │
└─────────────────┘    └───────────────────────────────┘             │
                          │ admin tasdiqlaydi (pending)              ▼
                          └──────────────→ Web sayt (Next.js) + Telegram
```

**Pipeline bosqichlari** ([`pipeline.py`](../backend/app/pipeline.py)):

1. **Yig'ish** — 5 ta feed'dan yangi xabarlar olinadi (`collect_news`).
2. **Futbol filtri** — `is_football_content()` URL va matn bo'yicha tekshiradi
   (Sky/Guardian/ESPN/BBC uchun URL darajasidagi qoidalar, aralash feed'lar uchun
   kalit so'z regex).
3. **Dublikat filtri (1-bosqich)** — `find_duplicate_article()` raw RSS
   bosqichida ayni voqeani topadi; topilsa yangi `ArticleSource` bog'lanadi,
   `IngestionDecision` yoziladi, maqola yaratilmaydi.
4. **AI tahlil** — `analyze_news()` bitta so'rovda quyidagilarni qaytaradi:
   `kategoriya`, `sarlavha`, `seo_sarlavha`, `xulosa`, `maqola`,
   `amaliy_ahamiyat`, `teglar`, `ahamiyati`, `entities`, `facts`, `event_key`,
   uchala confidence balli. Javob JSON sxema bilan kafolatlanadi.
5. **Kategoriya override** — `infer_category()` AI kategoriyasini kontekstga
   qarab qayta tekshiradi (O'zbekiston konteksti, transfer inkori/inkor
   farqlash, liga qoidalari). O'zgartirilsa `category_confidence` pastga
   tushiriladi.
6. **Dublikat filtri (2-bosqich)** — tarjima qilingan sarlavha va xulosa
   ishtirokida yana tekshiriladi (raw RSS bosqichida ko'rinmagan dublikatlarni
   ushlash uchun).
7. **Quality gate** — `analysis_is_publishable()`: uzunliklar, shubhali matn,
   keraksiz katta harfli so'zlar, structured entities/facts, fakt dalillarining
   manbada mavjudligi, confidence chegaralari.
8. **Avto-nashr gate** — `analysis_is_auto_publishable()`: qat'iy 90+ confidence,
   HTTPS ishonchli manba, ishonchli manbalar ro'yxati, ahamiyat minimumi.
9. **Saqlash** — `Article` + `ArticleQuality` + `ArticleSource` +
   `IngestionDecision`; `AUTO_PUBLISH=true` bo'lsa darhol `published`,
   aks holda `pending` (admin tasdiqlaydi).
10. **Telegram** — `AUTO_TELEGRAM` va ahamiyat shartlari bajarilsa kanalga
    yuboriladi.

**Concurrency himoyasi** — `runtime_lock` PostgreSQL advisory lock orqali
pipeline/botning faqat bitta nusxasi ishlashini ta'minlaydi (Render zero-downtime
deploy vaqtida ikki instance birga ishlaganda muhim).

## 3. Ma'lumotlar modeli

([`models.py`](../backend/app/models.py))

- **Category** — kategoriyalar (slug + name), `seed.py` bilan ekiladi.
- **Article** — o'zbekcha kontent (title, seo_title, slug, summary, content,
  practical_note, tags, importance), asl manba (original_title/url/source_name),
  `status` (`pending`/`published`/`rejected`), `sent_to_telegram`, sanalar.
- **ArticleSource** — bitta canonical maqolani tasdiqlovchi asl manbalar
  (dublikat ma'lumotlar bitta maqolaga bog'lanadi).
- **ArticleQuality** — AI tahlili va publish gate qarorining audit izi
  (confidence'lar, event_key, entities, facts, decision, reasons).
- **IngestionDecision** — har bir RSS elementiga berilgan oxirgi qaror logi
  (`duplicate_event`, `non_football`, `ai_error`, `ready`, `needs_review`,
  `auto_published`).

## 4. Backend API

| Router | Prefix | Tavsif |
|---|---|---|
| [`news.py`](../backend/app/routers/news.py) | `/api/news` | `GET ""`, `/top`, `/digest`, `/trends`, `/search`, `/rss`, `/sitemap`, `/{slug}` |
| [`categories.py`](../backend/app/routers/categories.py) | `/api/categories` | Kategoriyalar ro'yxati |
| [`admin.py`](../backend/app/routers/admin.py) | `/api/admin` | Maqolalar, ingestion log, tahrirlash, approve/reject, Telegramga yuborish, stats |
| [`scores.py`](../backend/app/routers/scores.py) | `/api/scores` | Bugungi o'yinlar, turnirlar, jadval, liga profillari |

**Scores integratsiyasi**:
- football-data.org (bepul 10 so'rov/dak, xotirada kesh: o'yinlar 60s, jadval 1s).
- O'zbekiston Superligasi uchun API-Football + PFL (skrepyor).
- TheSportsDB — liga badge/bannerlar.

**Xavfsizlik**: Admin router `require_admin` dependency orqali
`X-Admin-Token` header bilan himoyalangan. CORS allowlist mavjud.

## 5. AI Agent

([`ai_agent.py`](../backend/app/services/ai_agent.py))

- **Provayderlar**: `gemini` (standart, REST `generateContent`),
  `vertex` (ADC/service account), `claude` (ixtiyoriy, requirements'da izohli).
- **Schema**: `ANALYSIS_SCHEMA` OpenAPI kichik to'plami bilan `responseMimeType:
  application/json` — javob strukturasi kafolatlanadi.
- **Validatsiya**: `_validate()` — ahamiyat 1-5, kategoriya enum'ga sig'dirish,
  confidence 0-100, `normalize_analysis()` bilan matn tozalash.

## 6. Sifat nazorati (Content Quality)

([`content_quality.py`](../backend/app/services/content_quality.py))

- **`is_football_content`** — manba URL va matn asosida futbol bo'lmagan
  xabarlarni rad etadi (F1, golf, tennis...).
- **`normalize_text`** — ko'p uchraydigan kodlash/imlo xatolarini tuzatadi
  (`Liverpoool`→`Liverpul`, mojibake tuzatishlar).
- **`analysis_is_publishable`** — qo'lda tekshiruvga yuborishdan oldingi
  minimal sifat darvozasi.
- **`analysis_is_auto_publishable`** — qat'iy avto-nashr darvozasi (90+ confidence,
  HTTPS + ishonchli manba, ahamiyat).
- **`infer_category`** — AI kategoriyasini kontekstual qayta tekshirish.
- **`cleanup_existing_articles`** — eski noto'g'ri sport xabarlarini yashiradi,
  matn xatolarini tuzatadi.

## 7. Frontend

- **Next.js 15 App Router**, Server Components, `apiGet()` SSR'da `API_URL_INTERNAL`
  (konteyner ichida), brauzerda `NEXT_PUBLIC_API_URL`.
- **Sahifalar**: `/` (hero + so'nggi yangiliklar + Top 10 + dayjest + trendlar +
  qidiruv), `/kategoriya/[slug]`, `/maqola/[slug]` (SEO meta + OpenGraph rasm),
  `/qidiruv`, `/jadval`, `/admin`, `/aloqa`, `/haqida`, `/maxfiylik`.
- **Route handlerlar**: `/api/news/rss`, `/news-sitemap.xml`, `/sitemap`,
  `/robots`, `/manifest`, PWA icon routes.
- **Komponentlar**: `Header` (kategoriya menyusi — tabletada gorizontal overflow
  muammosi NEXT_TASKS'da qayd etilgan), `ArticleCard`, `LiveScores`,
  `AdPlaceholder`, `SubscribePopup`, `PwaRegister`.
- **SEO**: `metadata`, JSON-LD (Organization/WebSite), NewsArticle, sitemap,
  RSS, Google Adsense + GA identifikatorlari.
- **Admin** [`admin/page.js`](../frontend/app/admin/page.js): token bilan kirish,
  maqolalar ro'yxati, tahrirlash, tasdiqlash, Telegramga yuborish, stats.

## 8. Telegram bot

([`bot/bot.py`](../bot/bot.py)) — aiogram 3:
- 📰 bugungi yangiliklar, 🗓 haftalik dayjest, 📂 kategoriyalar, 🔍 qidiruv,
  ⭐ saqlanganlar, 🔔 bildirishnomalar.
- Backend REST API'ga murojaat qiladi; `storage.py` orqali SQLite'da foydalanuvchi
  sozlamalari saqlanadi.

## 9. Deploy va konfiguratsiya

- **Docker Compose**: `db` (PostgreSQL 16), `backend`, `pipeline` (har
  `PIPELINE_INTERVAL` soniyada `python -m app.pipeline`), `frontend`, `bot`.
- **Render** ([`render.yaml`](../render.yaml)): production'da Vertex AI
  (`AI_PROVIDER=vertex`), PostgreSQL managed, `AUTO_PUBLISH=true`.
- **Kalit konfiguratsiya** ([`config.py`](../backend/app/config.py)): barcha
  darvozalar (confidence, ahamiyat, ishonchli manbalar) env orqali sozlanadi.

## 10. Testlar

([`tests/`](../backend/tests/)) — unittest:
- `test_content_quality.py` — futbol filtri, matn tozalash, quality gate,
  structured gate, auto-publish gate, kategoriya infer.
- `test_event_dedup.py` — dublikat aniqlash.
- `test_ingestion_log.py`, `test_admin_quality_contract.py`,
  `test_sitemap_contract.py`.

## 11. Kuzatilgan kuchli tomonlar

- Ko'p bosqichli dublikat filtri (raw + AI tahlilidan keyin) va event_key
  yondashuvi — bir voqeaning takrorlanishini oldini oladi.
- Structured faktlar + evidence tekshiruvi — AI gallyutsinatsiyasini cheklaydi.
- Confidence'lar va ishonchli manbalar ro'yxati bilan bosqichma-bosqich
  avto-nashr darvozasi.
- Konkurens xavfsizligi (advisory lock), ingestion qarorlar audit izi.
- Sinov to'plami mavjud, deploy'da mustahkam sozlangan.

## 12. Kuzatilgan xavflar / kamchiliklar

1. **Dublikat filtri hali ham qo'pol** — token asosidagi Jaccard/SequenceMatcher;
   uzun maqolalar va kontentga qarab noto'g'ri musbat/manfiy berishi mumkin.
   NEXT_TASKS'da birinchi o'ringa qo'yilgan.
2. **O'zbek tahrir sifati** — `TEXT_REPLACEMENTS` qo'lda tuzatishlar ro'yxati
   (404 qatorda) hajm jihatdan cheklangan; yagona nomlar lug'ati yo'q.
3. **Planshet menyusi** — `Header`'da kategoriya menyusi 640-1024px'da gorizontal
   overflow qiladi (NEXT_TASKS #3).
4. **Search** — SQL `ILIKE`-ga asoslangan, o'zbekcha so'z shakllari va
   alifbo o'zgarishlarini hisobga olmaydi.
5. **Rasm generatsiya** — `IMAGE_GENERATION` pullik, standart o'chiq; rasm
   bo'lmagan maqolalar emoji placeholder ko'rsatadi.
6. **Kesh** — scores uchun faqat protsess ichidagi xotira kesh; ko'p instance'da
   samarasiz (README'da Redis rejalashtirilgan).
7. **Jadval/indexes** — `Article` da ba'zi so'rovlar (`content`/`summary`
   LIKE) indekssiz; hajm oshganda sekinlashishi mumkin.

## 13. Tavsiya etilgan keyingi qadamlar (ustuvorlik tartibida)

1. **Dublikat filtrini mustahkamlash** — `event_key` va `entities`-ga asoslangan
   qo'shimcha solishtirish; NEXT_TASKS #1 mezonlariga testlar.
2. **O'zbekcha nomlar lug'ati** va tahrir validatorini kengaytirish (NEXT_TASKS #2).
3. **Planshet navigatsiyasini tuzatish** (NEXT_TASKS #3) — menyuni konteyner
   ichida gorizontal scroll qilish.
4. **Maqola sahifasini boyitish** — o'xshash xabarlar, muallif, tuzatish siyosati
   (NEXT_TASKS #4).
5. **Reklama bloklarini production holatiga keltirish** (NEXT_TASKS #5).
6. **SEO/tezlik yakuniy auditi** (NEXT_TASKS #6).
