import { ImageResponse } from "next/og";
import { apiGet } from "../../../lib/api";
import { Ball } from "../../../lib/pwa-icon";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt = "Futbol Xabar maqolasi";

export default async function OgImage({ params }) {
  const { slug } = await params;
  const article = await apiGet(`/api/news/${slug}`);

  const title = article?.seo_title || article?.title || "Futbol Xabar";
  const category = article?.category?.name || "futbol yangiliklari";
  const hasImage = article?.image_url?.startsWith("http");

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          background: "#052e16",
          fontFamily: "sans-serif",
        }}
      >
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            padding: 60,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 16,
            }}
          >
            <div style={{ display: "flex" }}>
              <Ball size={56} />
            </div>
            <div
              style={{
                display: "flex",
                gap: 10,
                color: "#e2e8f0",
                fontSize: 30,
                fontWeight: 700,
              }}
            >
              <span>Futbol</span>
              <span style={{ color: "#4ade80" }}>Xabar</span>
            </div>
          </div>

          <div
            style={{
              color: "white",
              fontSize: title.length > 90 ? 44 : 54,
              fontWeight: 700,
              lineHeight: 1.2,
              display: "block",
              lineClamp: 4,
            }}
          >
            {title}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div
              style={{
                background: "rgba(74,222,128,0.15)",
                color: "#4ade80",
                borderRadius: 999,
                padding: "8px 22px",
                fontSize: 26,
                fontWeight: 600,
              }}
            >
              {category}
            </div>
            <div style={{ color: "#64748b", fontSize: 24 }}>futbolxabar.uz</div>
          </div>
        </div>

        {hasImage && (
          <img
            src={article.image_url}
            width={420}
            height={630}
            style={{ objectFit: "cover" }}
          />
        )}
      </div>
    ),
    size
  );
}
