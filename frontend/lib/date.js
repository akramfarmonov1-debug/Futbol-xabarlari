const MONTHS = [
  "yanvar",
  "fevral",
  "mart",
  "aprel",
  "may",
  "iyun",
  "iyul",
  "avgust",
  "sentabr",
  "oktabr",
  "noyabr",
  "dekabr",
];

function tashkentDate(value) {
  if (!value) return null;
  const raw = String(value);
  const hasTimezone = /(?:Z|[+-]\d{2}:\d{2})$/i.test(raw);
  const parsed = new Date(hasTimezone ? raw : `${raw}Z`);
  if (Number.isNaN(parsed.getTime())) return null;
  return new Date(parsed.getTime() + 5 * 60 * 60 * 1000);
}

export function formatUzDate(value, { year = false } = {}) {
  const date = tashkentDate(value);
  if (!date) return "";
  const dayMonth = `${date.getUTCDate()}-${MONTHS[date.getUTCMonth()]}`;
  return year ? `${dayMonth}, ${date.getUTCFullYear()}` : dayMonth;
}

export function formatUzDateTime(value) {
  const date = tashkentDate(value);
  if (!date) return "";
  const hours = String(date.getUTCHours()).padStart(2, "0");
  const minutes = String(date.getUTCMinutes()).padStart(2, "0");
  return `${formatUzDate(value, { year: true })}, ${hours}:${minutes}`;
}
