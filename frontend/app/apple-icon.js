import { ImageResponse } from "next/og";
import { Ball } from "../lib/pwa-icon";

export const size = { width: 180, height: 180 };
export const contentType = "image/png";

export default function AppleIcon() {
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
          borderRadius: 36,
          gap: 10,
        }}
      >
        <Ball size={92} />
        <div
          style={{
            fontSize: 22,
            fontWeight: 700,
            color: "#4ade80",
            letterSpacing: 4,
          }}
        >
          XABAR
        </div>
      </div>
    ),
    size
  );
}
