import { SITE_URL } from "../lib/site";

export default function robots() {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
      },
    ],
    // Admin va qidiruv sahifalari o'z metadata'sida `noindex` beradi.
    // Ularni robots.txt orqali bloklasak, crawler noindex tegini ko'ra olmaydi.
    sitemap: [`${SITE_URL}/sitemap.xml`, `${SITE_URL}/news-sitemap.xml`],
  };
}
