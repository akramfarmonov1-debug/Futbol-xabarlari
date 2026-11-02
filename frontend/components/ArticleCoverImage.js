"use client";

import { useState } from "react";
import Image from "next/image";

/**
 * Maqola bosh rasmi uchun xavfsiz komponent.
 * Agar tashqi manba rasmi o'chirilgan, 404 yoki bloklangan bo'lsa,
 * singan qora quti o'rniga zamonaviy gradient va to'p belgisi ko'rsatiladi.
 */
export default function ArticleCoverImage({ src, alt }) {
  const [hasError, setHasError] = useState(false);

  if (!src || hasError) {
    return (
      <div className="relative mb-6 overflow-hidden rounded-2xl border border-slate-900 aspect-video w-full bg-gradient-to-br from-emerald-950/30 via-slate-950 to-slate-900 flex flex-col items-center justify-center p-6 text-center shadow-inner">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-3xl mb-3 shadow-lg">
          ⚽
        </div>
        <span className="text-xs font-semibold tracking-wider uppercase text-emerald-400/80 mb-1">
          Futbol Xabar
        </span>
        <p className="text-xs text-slate-400 max-w-md line-clamp-2 px-4">
          {alt}
        </p>
      </div>
    );
  }

  return (
    <div className="relative mb-6 overflow-hidden rounded-2xl border border-slate-900 aspect-video w-full bg-slate-950">
      <Image
        src={src}
        alt={alt}
        fill
        priority
        sizes="(max-width: 768px) 100vw, 672px"
        className="object-cover"
        onError={() => setHasError(true)}
      />
    </div>
  );
}
