import "./globals.css";
import Header from "../components/Header";
import PwaRegister from "../components/PwaRegister";
import SubscribePopup from "../components/SubscribePopup";
import { SITE_URL, SITE_NAME, SITE_ALT_NAMES } from "../lib/site";

const DESCRIPTION =
  "Jahon futbolining eng muhim yangiliklari — qisqa, tushunarli va o'zbek tilida. Premyer-liga, La Liga, Chempionlar ligasi, transferlar va O'zbekiston futboli.";

export const metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: `${SITE_NAME} — Jahon futboli yangiliklari o'zbek tilida`,
    template: `%s — ${SITE_NAME}`,
  },
  description: DESCRIPTION,
  applicationName: SITE_NAME,
  alternates: {
    canonical: "/",
    types: {
      "application/rss+xml": [
        { url: "/api/news/rss", title: `${SITE_NAME} RSS` },
      ],
    },
  },
  openGraph: {
    type: "website",
    url: "/",
    siteName: SITE_NAME,
    locale: "uz_UZ",
    title: `${SITE_NAME} — Jahon futboli yangiliklari o'zbek tilida`,
    description: DESCRIPTION,
  },
  twitter: {
    card: "summary_large_image",
    title: `${SITE_NAME} — Jahon futboli yangiliklari`,
    description: DESCRIPTION,
  },
  appleWebApp: {
    capable: true,
    title: "Futbol Xabar",
    statusBarStyle: "black-translucent",
  },
};

const siteJsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": `${SITE_URL}/#organization`,
      name: SITE_NAME,
      alternateName: SITE_ALT_NAMES,
      url: SITE_URL,
      logo: {
        "@type": "ImageObject",
        url: `${SITE_URL}/icon-512`,
        width: 512,
        height: 512,
      },
      sameAs: ["https://t.me/futbolxabarida"],
    },
    {
      "@type": "WebSite",
      "@id": `${SITE_URL}/#website`,
      name: SITE_NAME,
      alternateName: SITE_ALT_NAMES,
      url: SITE_URL,
      inLanguage: "uz",
      publisher: { "@id": `${SITE_URL}/#organization` },
      potentialAction: {
        "@type": "SearchAction",
        target: {
          "@type": "EntryPoint",
          urlTemplate: `${SITE_URL}/qidiruv?q={search_term_string}`,
        },
        "query-input": "required name=search_term_string",
      },
    },
  ],
};

export const viewport = {
  themeColor: "#14532d",
};


export default function RootLayout({ children }) {
  return (
    <html lang="uz">
      <body>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(siteJsonLd) }}
        />
        <Header />
        <main className="mx-auto max-w-6xl px-4 pb-16">{children}</main>
        <footer className="border-t border-slate-800 py-8 text-center text-sm text-slate-500">
          <div className="mb-3 flex justify-center gap-4 flex-wrap">
            <a href="/haqida" className="text-slate-400 hover:text-white transition-colors">
              Biz haqimizda
            </a>
            <span>•</span>
            <a href="/aloqa" className="text-slate-400 hover:text-white transition-colors">
              Aloqa
            </a>
            <span>•</span>
            <a href="/maxfiylik" className="text-slate-400 hover:text-white transition-colors">
              Maxfiylik
            </a>
            <span>•</span>
            <a
              href="https://t.me/futbolxabarida"
              target="_blank"
              rel="noopener noreferrer"
              className="text-slate-400 hover:text-sky-400 transition-colors"
            >
              📢 Telegram Kanal (@futbolxabarida)
            </a>
            <span>•</span>
            <a
              href="https://t.me/Futbolxabar_bot"
              target="_blank"
              rel="noopener noreferrer"
              className="text-slate-400 hover:text-green-400 transition-colors"
            >
              🤖 Telegram Bot (@Futbolxabar_bot)
            </a>
          </div>
          © {new Date().getFullYear()} Futbol Xabar (futbolxabar.uz) — jahon futboli yangiliklari o&apos;zbek tilida
        </footer>
        <SubscribePopup />
        <PwaRegister />
      </body>
    </html>
  );
}
