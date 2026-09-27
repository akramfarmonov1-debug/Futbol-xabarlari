// Server (SSR) konteyner ichida backend'ga ichki tarmoq orqali murojaat qiladi
// (API_URL_INTERNAL), brauzer esa tashqi manzildan (NEXT_PUBLIC_API_URL).
const isServer = typeof window === "undefined";
const API_URL =
  (isServer && process.env.API_URL_INTERNAL) ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

// Backend javob bermasa sahifa osilib qolmasin. O'lik Render instance ulanishni
// ochiq ushlab turadi, fetch esa standart holatda 5 daqiqagacha kutadi — shuncha
// vaqt har bir sahifa ko'rilishida Vercel funksiyasi band bo'lib, bepul tarif
// limitini yeydi.
const API_TIMEOUT_MS = 5_000;

export class ApiUnavailableError extends Error {
  name = "ApiUnavailableError";
}

// 404 → null; backend yiqilgan yoki javob bermasa → ApiUnavailableError.
// "Bunday narsa yo'q" bilan "hozir bilib bo'lmaydi"ni ajratish kerak bo'lgan
// joylar uchun: masalan, maqola sahifasi uzilish paytida "topilmadi" (noindex)
// desa, maqolalar qidiruv tizimidan tushib ketadi.
export async function apiGetOrThrow(path, params = {}) {
  const url = new URL(`${API_URL}${path}`);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) url.searchParams.set(key, value);
  });
  let res;
  try {
    res = await fetch(url, {
      cache: "no-store",
      signal: AbortSignal.timeout(API_TIMEOUT_MS),
    });
  } catch (error) {
    throw new ApiUnavailableError(`${path}: ${error.name}`);
  }
  if (res.status >= 500) {
    throw new ApiUnavailableError(`${path}: HTTP ${res.status}`);
  }
  if (!res.ok) return null;
  return res.json();
}

// Har qanday xatoda null. Ro'yxatlarda null bilan [] farqli: null — backend
// javob bermadi, [] — haqiqatan bo'sh; sahifalar xabarni shunga qarab tanlaydi.
export async function apiGet(path, params = {}) {
  try {
    return await apiGetOrThrow(path, params);
  } catch {
    return null;
  }
}

export { API_URL, API_TIMEOUT_MS };
