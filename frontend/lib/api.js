// Server (SSR) konteyner ichida backend'ga ichki tarmoq orqali murojaat qiladi
// (API_URL_INTERNAL), brauzer esa tashqi manzildan (NEXT_PUBLIC_API_URL).
const isServer = typeof window === "undefined";
const API_URL =
  (isServer && process.env.API_URL_INTERNAL) ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

export async function apiGet(path, params = {}) {
  const url = new URL(`${API_URL}${path}`);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) url.searchParams.set(key, value);
  });
  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export { API_URL };
