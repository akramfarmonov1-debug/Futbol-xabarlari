// Saytning tashqi (kanonik) manzili — SEO, sitemap, OG teglar uchun
const configuredSiteUrl =
  process.env.NEXT_PUBLIC_SITE_URL || "https://www.futbolxabar.uz";

export const SITE_URL = configuredSiteUrl
  .replace(
    /^https:\/\/futbolxabar\.uz(?=\/|$)/,
    "https://www.futbolxabar.uz",
  )
  .replace(/\/+$/, "");

export const SITE_NAME = "Futbol Xabar";
export const SITE_ALT_NAMES = ["Futbol Yangiliklari", "Futbol Xabar Uzbekistan"];
