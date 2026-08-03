# 🤖 Futbol Xabar

Dunyodagi muhim futbol yangiliklarini ishonchli manbalardan **yig'ib**, AI yordamida **o'zbek tiliga moslashtirib**, sifat nazoratidan keyin **web sayt** va **Telegram bot** orqali yetkazuvchi platforma.

## Arxitektura

```
┌─────────────────┐     ┌──────────────────────┐     ┌───────────────┐
│  RSS manbalar   │ --> │  AI Agent (pipeline) │ --> │  PostgreSQL / │
│ BBC, Guardian,   │     │  yig'ish → dublikat  │     │    SQLite     │
│ Sky, ESPN, ...  │     │  → fakt tekshiruvi   │     │  (pending)    │
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
| Yangiliklar yig'uvchi | RSS/Atom parser + event dublikat filtri | `backend/app/services/collector.py` |
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
- `amaliy_ahamiyat` — "Bu nima degani?" (muxlis va jamoa istiqboli uchun)
- `teglar` — 3-6 ta teg
- `ahamiyati` — 1-5 baho
- `entities` va `facts` — kanonik nomlar, structured faktlar va manbadagi dalil
- `football_confidence`, `category_confidence`, `fact_confidence` — 0-100 sifat ballari
- `event_key` — bir voqeani boshqa RSS manbalari bilan bog'lash kaliti

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

**Moderatsiya rejimi (standart, `AUTO_PUBLISH=false`):**

1. Backend fon pipeline'ini `PIPELINE_INTERVAL` bo'yicha ishga tushiradi
2. RSS'dan yangi xabarlar yig'iladi; ayni voqeaning boshqa manbasi yangi URL yaratmasdan canonical maqolaga bog'lanadi
3. AI structured fakt, manbadagi evidence va confidence ballarini qaytaradi; validator kategoriya va dalillarni tekshiradi
4. Maqola `pending` holatida saqlanadi, admin sifat sabablarini ko'rib tasdiqlaydi yoki rad etadi

Render zero-downtime deploy vaqtida eski va yangi instance qisqa muddat birga
ishlasa ham PostgreSQL advisory lock bot va pipeline'ning faqat bitta nusxasini
faol qoldiradi.

Sozlamalar (`.env`):

| O'zgaruvchi | Standart | Tavsif |
|---|---|---|
| `AUTO_PUBLISH` | `false` | Faqat quality gate'dan o'tgan maqolalarni avtomatik chiqarish uchun `true` qiling |
| `AUTO_PUBLISH_MIN_IMPORTANCE` | `1` | Shu bahodan pastlari `pending`da qoladi |
| `MIN_FOOTBALL_CONFIDENCE` | `85` | Futbolga aloqadorlik uchun minimal confidence |
| `MIN_CATEGORY_CONFIDENCE` | `75` | Kategoriya uchun minimal confidence |
| `MIN_FACT_CONFIDENCE` | `80` | Faktlar uchun minimal confidence |
| `AUTO_TELEGRAM` | `false` | Muhim yangiliklarni kanalga avto-yuborish |
| `AUTO_TELEGRAM_MIN_IMPORTANCE` | `4` | Kanalga yuborish uchun minimal baho |
| `PIPELINE_INTERVAL` | `3600` | Pipeline qayta ishga tushish oralig'i, soniyada |
| `MAX_NEWS_AGE_DAYS` | `3` | RSS'dan olinadigan xabarlarning maksimal yoshi |

**Avtomatik rejim (`AUTO_PUBLISH=true`)** faqat structured quality gate'dan o'tgan materiallarni chiqaradi. Kategoriya override, past confidence yoki manbada topilmagan fakt dalili maqolani baribir `pending` holatida qoldiradi.

## Kelajakdagi rejalar (TZ bo'yicha)

- Redis kesh, email obuna, push bildirishnomalar
- Legionerlar kuzatuvi, transfer tracker, klub va futbolchi sahifalari
- Ovozli dayjest, YouTube Shorts, avtomatik SMM postlar
- Premium obuna va reklama moduli
- Mobil ilova
