import "./globals.css";
import Header from "../components/Header";
import PwaRegister from "../components/PwaRegister";
import SubscribePopup from "../components/SubscribePopup";
import { SITE_URL, SITE_NAME, SITE_ALT_NAMES } from "../lib/site";
import Script from "next/script";
import { Outfit } from "next/font/google";

const outfit = Outfit({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
  display: "swap",
});

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
  verification: {
    google: "--9CvR3hkmw5cyoj7o1Mi9IDD8m-Mr_D1h0hXx2I510",
  },
  other: {
    "google-adsense-account": "ca-pub-7905311764554890",
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
  themeColor: "#0f172a",
};

export default function RootLayout({ children }) {
  const gaId = process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID;
  const adsenseClientId = process.env.NEXT_PUBLIC_ADSENSE_CLIENT_ID;
  return (
    <html lang="uz" className={outfit.className}>
      <body className="selection:bg-emerald-500 selection:text-slate-950">
        {gaId && (
          <>
            <Script
              src={`https://www.googletagmanager.com/gtag/js?id=${gaId}`}
              strategy="afterInteractive"
            />
            <Script id="google-analytics" strategy="afterInteractive">
              {`
                window.dataLayer = window.dataLayer || [];
                function gtag(){dataLayer.push(arguments);}
                gtag('js', new Date());
                gtag('config', '${gaId}');
              `}
            </Script>
          </>
        )}
        {adsenseClientId && (
          <Script
            async
            src={`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${adsenseClientId}`}
            crossOrigin="anonymous"
            strategy="afterInteractive"
          />
        )}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(siteJsonLd) }}
        />
        
        {/* Main Content Layout */}
        <div className="flex min-h-screen flex-col">
          <Header />
          <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 md:py-10">
            {children}
          </main>
          
          <footer className="border-t border-slate-900 bg-slate-950/80 py-10 text-center text-sm text-slate-500 backdrop-blur-md">
            <div className="mx-auto max-w-6xl px-4">
              <div className="mb-6 flex flex-wrap justify-center gap-x-6 gap-y-3 font-medium">
                <a href="/haqida" className="text-slate-400 hover:text-emerald-400 transition-colors">
                  Biz haqimizda
                </a>
                <span className="text-slate-800 hidden sm:inline">|</span>
                <a href="/aloqa" className="text-slate-400 hover:text-emerald-400 transition-colors">
                  Aloqa
                </a>
                <span className="text-slate-800 hidden sm:inline">|</span>
                <a href="/maxfiylik" className="text-slate-400 hover:text-emerald-400 transition-colors">
                  Maxfiylik kelishuvi
                </a>
              </div>
              <p className="mb-4 text-xs max-w-md mx-auto leading-relaxed">
                Loyihadagi barcha xabarlar AI (Sun&apos;iy intellekt) yordamida o&apos;zbek tiliga tushunarli qilib tarjima qilingan va tayyorlangan.
              </p>
              <div className="text-xs text-slate-600">
                © {new Date().getFullYear()} Futbol Xabar (futbolxabar.uz) · Barcha huquqlar himoyalangan.
              </div>
            </div>
          </footer>
        </div>

        {/* Mobile Sticky Navigation Bar */}
        <div className="fixed bottom-0 left-0 right-0 z-40 block border-t border-slate-900 bg-slate-950/90 py-2.5 backdrop-blur-lg md:hidden">
          <div className="flex items-center justify-around px-2">
            <a href="/" className="flex flex-col items-center gap-1 text-slate-400 hover:text-emerald-400 transition-colors">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
              <span className="text-[10px] font-semibold">Asosiy</span>
            </a>
            
            <a href="/jadval" className="flex flex-col items-center gap-1 text-slate-400 hover:text-emerald-400 transition-colors">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
              </svg>
              <span className="text-[10px] font-semibold">Jadval</span>
            </a>

            <a href="/qidiruv" className="flex flex-col items-center gap-1 text-slate-400 hover:text-emerald-400 transition-colors">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <span className="text-[10px] font-semibold">Qidiruv</span>
            </a>

            <a href="https://t.me/futbolxabarida" target="_blank" rel="noopener noreferrer" className="flex flex-col items-center gap-1 text-slate-400 hover:text-sky-400 transition-colors">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <span className="text-[10px] font-semibold">Telegram</span>
            </a>
          </div>
        </div>

        <SubscribePopup />
        <PwaRegister />
      </body>
    </html>
  );
}
