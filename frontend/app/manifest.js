export default function manifest() {
  return {
    name: "Futbol Xabar — Jahon futboli yangiliklari",
    short_name: "Futbol Xabar",
    description:
      "Dunyodagi eng muhim futbol yangiliklari — qisqa, tushunarli va o'zbek tilida.",
    start_url: "/",
    display: "standalone",
    background_color: "#052e16",
    theme_color: "#14532d",
    lang: "uz",
    categories: ["news", "technology"],
    icons: [
      {
        src: "/icon-192",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icon-512",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icon-512",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
