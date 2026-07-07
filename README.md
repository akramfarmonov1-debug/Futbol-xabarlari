# 🤖 Futbol Xabar

Sun'iy intellektga oid eng muhim yangiliklarni dunyodagi ishonchli manbalardan **avtomatik yig'ib**, AI yordamida **o'zbek tiliga moslashtirib**, **web sayt** va **Telegram bot** orqali yetkazib beruvchi platforma (MVP).

## Arxitektura

```
┌─────────────────┐     ┌──────────────────────┐     ┌───────────────┐
│  RSS manbalar   │ --> │  AI Agent (pipeline) │ --> │  PostgreSQL / │
│ BBC, Guardian,   │     │  yig'ish → dublikat  │     │    SQLite     │
│ TechCrunch, ... │     │  → Claude tahlili    │     │  (pending)    │
└─────────────────┘     └──────────────────────┘     └───────┬───────┘
                                                             │ admin tasdiqlaydi
                        ┌──────────────┐    ┌────────────────┼────────────────┐
                        │ Admin panel  │ -->│                ▼                │
                        └──────────────┘    │  Web sayt (Next.js)             │
                                            │  Telegram kanal + bot (aiogram) │
                                            └─────────────────────────────────┘
```

| Qism | Texnologiya | Papka |
|---|---|---|
| Backend + REST API | FastAPI, SQLAlchemy, PostgreSQL/SQLite | `backend/` |
| AI Agent | Gemini API (standart) yoki Claude API — strukturali JSON | `backend/app/services/ai_agent.py` |
| Yangiliklar yig'uvchi | feedparser (RSS) + dublikat filtri | `backend/app/services/collector.py` |
| Frontend | Next.js 15, React 19, Tailwind CSS 4 | `frontend/` |
| Admin panel | Next.js sahifasi (`/admin`) + Admin API | `frontend/app/admin/` |
| Telegram bot | aiogram 3 | `bot/` |

## AI Agent nima qiladi?

Har bir inglizcha yangilik uchun AI model (standart: **Gemini `gemini-3.1-flash-lite`** — arzon va tez; `.env`da `AI_PROVIDER=claude` qilib Claude'ga o'tish mumkin) quyidagilarni **bitta so'rovda** tayyorlaydi (javob JSON sxema bilan kafolatlanadi):

- `kategoriya` — Transferlar, Premyer-liga, La Liga, Seriya A, Bundesliga, Chempionlar ligasi, Jahon futboli, O'zbekiston futboli, Terma jamoalar
- `sarlavha` — o'zbekcha sarlavha
- `seo_sarlavha` — SEO uchun optimallashtirilgan sarlavha
- `xulosa` — 3-5 jumlalik qisqa xulosa
- `maqola` — to'liq o'zbekcha maqola (3-6 paragraf)
- `amaliy_ahamiyat` — "Bu nima degani?" (dasturchilar/biznes uchun)
- `teglar` — 3-6 ta teg
- `ahamiyati` — 1-5 baho

Maqolalar `pending` holatida saqlanadi — **admin tasdiqlagachgina** saytga chiqadi.

---

## ⚡ Eng oson yo'l: Docker Compose (tavsiya etiladi)

Butun platforma (PostgreSQL + backend + AI pipeline + sayt + bot) bitta buyruq bilan:

```bash
cp .env.example .env      # GEMINI_API_KEY, ADMIN_TOKEN, TELEGRAM_* ni to'ldiring
docker compose up -d --build
```

Shundan so'ng:
- Sayt: http://localhost:3000 (admin: http://localhost:3000/admin)
- API: http://localhost:8000/docs
- Pipeline har soatda (`PIPELINE_INTERVAL`) avtomatik yangiliklarni yig'ib chop etadi
- Bot `TELEGRAM_BOT_TOKEN` kiritilgan bo'lsa avtomatik ishlaydi

Loglarni ko'rish: `docker compose logs -f pipeline` · To'xtatish: `docker compose down`

Serverga qo'yganda `.env`da `NEXT_PUBLIC_API_URL`, `FRONTEND_ORIGIN`, `SITE_URL` qiymatlarini o'z domeningizga almashtiring.

---

Quyida har bir qismni Docker'siz, alohida ishga tushirish yo'riqnomasi.

## 1. Backend'ni ishga tushirish

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # GEMINI_API_KEY, ADMIN_TOKEN va boshqalarni to'ldiring

# Serverni ishga tushirish (http://localhost:8000, hujjatlar: /docs)
uvicorn app.main:app --reload
```

**Yangiliklarni yig'ish va tahlil qilish** (qo'lda yoki cron orqali):

```bash
python -m app.pipeline
```

Muntazam avtomatik ishlashi uchun cron misoli (har soatda):

```cron
0 * * * * cd /path/backend && .venv/bin/python -m app.pipeline
```

## 2. Frontend'ni ishga tushirish

```bash
cd frontend
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL
npm run dev                  # http://localhost:3000
```

Sahifalar:
- `/` — so'nggi yangiliklar, Top 10, bugungi dayjest, trend mavzular, qidiruv
- `/kategoriya/[slug]` — kategoriya bo'yicha
- `/maqola/[slug]` — to'liq maqola (SEO meta, teglar, ulashish)
- `/qidiruv?q=...` — qidiruv
- `/admin` — admin panel (token bilan kirish)

## 3. Telegram botni ishga tushirish

```bash
cd bot
pip install -r requirements.txt
cp .env.example .env         # TELEGRAM_BOT_TOKEN, API_URL
python bot.py
```

Bot funksiyalari: 📰 bugungi yangiliklar · 🗓 haftalik dayjest · 📂 kategoriyalar · 🔍 qidiruv · ⭐ saqlanganlar · 🔔 bildirishnomalar.

## REST API (asosiy endpointlar)

| Metod | Yo'l | Tavsif |
|---|---|---|
| GET | `/api/news` | So'nggi yangiliklar (`kategoriya`, `limit`, `offset`) |
| GET | `/api/news/top` | Top yangiliklar (`kunlar`, `limit`) |
| GET | `/api/news/digest` | Bugungi dayjest |
| GET | `/api/news/trends` | Trend teglar |
| GET | `/api/news/search?q=` | Qidiruv |
| GET | `/api/news/{slug}` | Bitta maqola |
| GET | `/api/categories` | Kategoriyalar |
| GET | `/api/admin/articles` | Admin: maqolalar ro'yxati (`X-Admin-Token`) |
| PUT | `/api/admin/articles/{id}` | Admin: tahrirlash |
| POST | `/api/admin/articles/{id}/approve` | Admin: tasdiqlash → saytga chiqarish |
| POST | `/api/admin/articles/{id}/telegram` | Admin: Telegram kanaliga yuborish |
| DELETE | `/api/admin/articles/{id}` | Admin: o'chirish |
| GET | `/api/admin/stats` | Admin: statistika |

To'liq interaktiv hujjatlar: `http://localhost:8000/docs`

## Ish oqimi (workflow)

**Avtomatik rejim (standart, `AUTO_PUBLISH=true`):**

1. Cron har soatda `python -m app.pipeline` ni ishga tushiradi
2. RSS'dan yangiliklar yig'iladi, dublikatlar filtrlanadi, Claude har birini o'zbekcha maqolaga aylantiradi
3. Maqolalar **darhol saytga chiqadi**; muhimlari (bahosi ≥ `AUTO_TELEGRAM_MIN_IMPORTANCE`, standart 4) **Telegram kanalga ham avtomatik yuboriladi**
4. Admin `/admin` panelda faqat nazorat qiladi: xato maqolani tahrirlaydi yoki o'chiradi

Sozlamalar (`.env`):

| O'zgaruvchi | Standart | Tavsif |
|---|---|---|
| `AUTO_PUBLISH` | `true` | `false` — maqolalar admin tasdig'ini kutadi |
| `AUTO_PUBLISH_MIN_IMPORTANCE` | `1` | Shu bahodan pastlari `pending`da qoladi |
| `AUTO_TELEGRAM` | `true` | Muhim yangiliklarni kanalga avto-yuborish |
| `AUTO_TELEGRAM_MIN_IMPORTANCE` | `4` | Kanalga yuborish uchun minimal baho |

**Moderatsiya rejimi (`AUTO_PUBLISH=false`):** maqolalar `pending` holatda saqlanadi, admin `/admin` sahifasida ko'rib **Tasdiqlash** bosgachgina saytga chiqadi va **Telegramga** tugmasi bilan kanalga yuboradi.

## Kelajakdagi rejalar (TZ bo'yicha)

- Redis kesh, email obuna, push bildirishnomalar
- AI Tool katalogi, tadbirlar taqvimi, ish o'rinlari, kurslar
- Ovozli dayjest, YouTube Shorts, avtomatik SMM postlar
- Premium obuna va reklama moduli
- Mobil ilova
