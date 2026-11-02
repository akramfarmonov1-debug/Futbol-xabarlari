"use client";

const FAVORITE_CLUB_KEY = "futbolxabar_favorite_club";

export function getFavoriteClub() {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(FAVORITE_CLUB_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function saveFavoriteClub(club) {
  if (typeof window === "undefined") return;
  try {
    if (!club) {
      localStorage.removeItem(FAVORITE_CLUB_KEY);
    } else {
      localStorage.setItem(FAVORITE_CLUB_KEY, JSON.stringify(club));
    }
    window.dispatchEvent(new CustomEvent("favorite_club_changed", { detail: club }));
  } catch {
    // pass
  }
}
