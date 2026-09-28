"use client";

import { useEffect } from "react";
import { API_URL } from "../lib/api";

// Maqola sahifasi keshlanadi (ISR) va daqiqada ko'pi bilan bir marta yasaladi,
// shuning uchun ko'rish server render'ida emas, brauzerdan alohida sanaladi.
export default function ViewTracker({ slug }) {
  useEffect(() => {
    fetch(`${API_URL}/api/news/${encodeURIComponent(slug)}/view`, {
      method: "POST",
      keepalive: true,
    }).catch(() => {});
  }, [slug]);

  return null;
}
