/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  // Vercel Hobby oyiga 5000 ta rasm transformatsiyasi beradi: har bir noyob
  // rasm × kenglik × format bittadan. Kichik gerb va belgilar umuman
  // optimizatsiya qilinmaydi (unoptimized), qolganlari uchun:
  images: {
    // Bitta format: AVIF qo'shilsa har rasm ikki marta qayta ishlanadi.
    formats: ["image/webp"],
    // Yangilik rasmlari bir manzilda o'zgarmaydi — 31 kun keshda turadi,
    // har kuni qaytadan ishlanmaydi (avval 1 kun edi).
    minimumCacheTTL: 2678400,
    // Kamroq kenglik varianti: bir rasm uchun kamroq transformatsiya
    // (standart 16 xil kenglik o'rniga 7 xil).
    deviceSizes: [640, 828, 1200, 1920],
    imageSizes: [128, 256, 384],
    remotePatterns: [
      // Liga bannerlari (jadval sahifasi). Ro'yxatda yo'qligi uchun
      // optimizator ularni 400 bilan rad etib kelgan.
      { protocol: "https", hostname: "r2.thesportsdb.com" },
      { protocol: "https", hostname: "ichef.bbci.co.uk" },
      { protocol: "https", hostname: "i.guim.co.uk" },
      { protocol: "https", hostname: "*.365dm.com" },
      { protocol: "https", hostname: "*.espncdn.com" },
      { protocol: "https", hostname: "media.sports.uz" },
      { protocol: "https", hostname: "cdn.pfl.uz" },
      { protocol: "https", hostname: "crests.football-data.org" },
      { protocol: "https", hostname: "upload.wikimedia.org" },
      {
        protocol: "https",
        hostname: "futbol-xabar-backend.onrender.com",
      },
    ],
  },
};

export default nextConfig;
