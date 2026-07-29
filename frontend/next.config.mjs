/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  images: {
    formats: ["image/avif", "image/webp"],
    minimumCacheTTL: 86400,
    remotePatterns: [
      { protocol: "https", hostname: "ichef.bbci.co.uk" },
      { protocol: "https", hostname: "i.guim.co.uk" },
      { protocol: "https", hostname: "*.365dm.com" },
      { protocol: "https", hostname: "*.espncdn.com" },
      { protocol: "https", hostname: "media.sports.uz" },
      { protocol: "https", hostname: "cdn.pfl.uz" },
      { protocol: "https", hostname: "*.thesportsdb.com" },
      {
        protocol: "https",
        hostname: "futbol-xabar-backend.onrender.com",
      },
    ],
  },
};

export default nextConfig;
