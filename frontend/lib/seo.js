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
