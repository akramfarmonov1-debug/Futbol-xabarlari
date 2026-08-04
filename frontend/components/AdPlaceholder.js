"use client";

// Reklama provayderi (Google AdSense) faqat NEXT_PUBLIC_ADSENSE_CLIENT_ID
// sozlangan bo'lsa ishlaydi. Provayder ulangan bo'lmasa, placeholder
// foydalanuvchiga umuman ko'rinmaydi (sahifa toza bo'ladi).
const ADSENSE_CLIENT = process.env.NEXT_PUBLIC_ADSENSE_CLIENT_ID || "";
const ADSENSE_SLOT = process.env.NEXT_PUBLIC_ADSENSE_SLOT_ID || "";

// O'lchamlar: mobil va desktop uchun alohida, layout siljishini (CLS)
// oldini olish uchun joy oldindan band qilinadi.
const SIZES = {
  sidebar: { minHeight: 250, className: "hidden sm:block" },
  banner: { minHeight: 50, className: "" },
};

export default function AdPlaceholder({ type = "sidebar" }) {
  if (!ADSENSE_CLIENT) return null;

  const size = SIZES[type] || SIZES.sidebar;

  return (
    <div className="w-full">
      {/* Joy oldindan band qilinadi — reklama yuklanganda siljish bo'lmaydi. */}
      <div
        className="flex min-h-full w-full items-center justify-center overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40"
        style={{ minHeight: size.minHeight }}
      >
        <ins
          className="adsbygoogle block"
          style={{ display: "block" }}
          data-ad-client={ADSENSE_CLIENT}
          data-ad-slot={ADSENSE_SLOT || undefined}
          data-ad-format="auto"
          data-full-width-responsive="true"
        />
      </div>
      <script
        dangerouslySetInnerHTML={{
          __html: "(adsbygoogle = window.adsbygoogle || []).push({});",
        }}
      />
    </div>
  );
}
