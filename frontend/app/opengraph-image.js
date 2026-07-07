import { ImageResponse } from "next/og";
import { Ball } from "../lib/pwa-icon";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt = "Futbol Xabar — Jahon futboli yangiliklari";

export default function OgImage() {
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
          fontFamily: "sans-serif",
          gap: 30,
        }}
      >
        <Ball size={130} />
        <div
          style={{
            display: "flex",
            gap: 18,
            color: "white",
            fontSize: 68,
            fontWeight: 700,
          }}
        >
          <span>Futbol</span>
          <span style={{ color: "#4ade80" }}>Xabar</span>
        </div>
        <div style={{ color: "#a7f3d0", fontSize: 32 }}>
          Jahon futboli yangiliklari — o&apos;zbek tilida
        </div>
        <div style={{ color: "#4d7c0f", fontSize: 28 }}>futbolxabar.uz</div>
      </div>
    ),
    size
  );
}
