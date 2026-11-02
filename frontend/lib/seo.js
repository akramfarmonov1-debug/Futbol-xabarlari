export function truncateSeoText(value, maxLength) {
  const text = String(value || "")
    .replace(/\s+/g, " ")
    .trim();

  if (text.length <= maxLength) return text;

  const sliced = text.slice(0, maxLength - 1);
  const wordBoundary = sliced.lastIndexOf(" ");
  const shortened =
    wordBoundary >= Math.floor(maxLength * 0.65)
      ? sliced.slice(0, wordBoundary)
      : sliced;

  return `${shortened.trimEnd()}…`;
}

export function tagSlug(tag) {
  return String(tag || "")
    .toLowerCase()
    .replace(/['’ʼʻ`´]/g, "")
    .replace(/[^a-z0-9\u0400-\u04ff]+/g, "-")
    .replace(/^-+|-+$/g, "");
}
