import { ImageResponse } from "next/og";

// Soddalashtirilgan futbol koptogi (satori inline SVG qo'llaydi)
function Ball({ size }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40">
      <circle cx="20" cy="20" r="18" fill="#ffffff" />
      <polygon points="20,11 28.6,17.3 25.3,27.4 14.7,27.4 11.4,17.3" fill="#052e16" />
      <line x1="20" y1="11" x2="20" y2="2" stroke="#052e16" strokeWidth="2.2" />
      <line x1="28.6" y1="17.3" x2="37" y2="14.4" stroke="#052e16" strokeWidth="2.2" />
      <line x1="25.3" y1="27.4" x2="30.5" y2="34.7" stroke="#052e16" strokeWidth="2.2" />
      <line x1="14.7" y1="27.4" x2="9.5" y2="34.7" stroke="#052e16" strokeWidth="2.2" />
      <line x1="11.4" y1="17.3" x2="3" y2="14.4" stroke="#052e16" strokeWidth="2.2" />
    </svg>
  );
}

export { Ball };

// PWA manifest uchun PNG ikon generatori (192/512)
export function pwaIcon(px) {
  const s = px / 192; // 192 ga nisbatan masshtab
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background: "#052e16",
          gap: 12 * s,
        }}
      >
        <Ball size={96 * s} />
        <div
          style={{
            fontSize: 24 * s,
            fontWeight: 700,
            color: "#4ade80",
            letterSpacing: 4 * s,
          }}
        >
          XABAR
        </div>
      </div>
    ),
    { width: px, height: px }
  );
}
