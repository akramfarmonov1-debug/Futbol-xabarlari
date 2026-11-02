import Link from "next/link";
import { tagSlug } from "./seo";

const LEGIONNAIRE_KEYWORDS = [
  { name: "Abduqodir Husanov", slug: "abduqodir-husanov", path: "/legionerlar/abduqodir-husanov" },
  { name: "Husanov", slug: "abduqodir-husanov", path: "/legionerlar/abduqodir-husanov" },
  { name: "Abbosbek Fayzullayev", slug: "abbosbek-fayzullayev", path: "/legionerlar/abbosbek-fayzullayev" },
  { name: "Fayzullayev", slug: "abbosbek-fayzullayev", path: "/legionerlar/abbosbek-fayzullayev" },
  { name: "Eldor Shomurodov", slug: "eldor-shomurodov", path: "/legionerlar/eldor-shomurodov" },
  { name: "Shomurodov", slug: "eldor-shomurodov", path: "/legionerlar/eldor-shomurodov" },
  { name: "Oston O'runov", slug: "oston-orunov", path: "/legionerlar/oston-orunov" },
  { name: "O'runov", slug: "oston-orunov", path: "/legionerlar/oston-orunov" },
  { name: "Jaloliddin Masharipov", slug: "jaloliddin-masharipov", path: "/legionerlar/jaloliddin-masharipov" },
  { name: "Masharipov", slug: "jaloliddin-masharipov", path: "/legionerlar/jaloliddin-masharipov" },
  { name: "Azizjon G'aniyev", slug: "azizjon-ganiyev", path: "/legionerlar/azizjon-ganiyev" },
  { name: "G'aniyev", slug: "azizjon-ganiyev", path: "/legionerlar/azizjon-ganiyev" },
];

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function linkifyParagraph(paragraph, tags = [], linkedKeywords = new Set()) {
  if (!paragraph || typeof paragraph !== "string") return paragraph;

  // 1. Legionerlar va maqola teglari birlashtiriladi
  const targets = [];

  for (const leg of LEGIONNAIRE_KEYWORDS) {
    if (!linkedKeywords.has(leg.name.toLowerCase())) {
      targets.push({
        phrase: leg.name,
        href: leg.path,
        key: leg.name.toLowerCase(),
      });
    }
  }

  for (const rawTag of tags || []) {
    const slug = tagSlug(rawTag);
    const key = String(rawTag).trim().toLowerCase();
    if (slug && key.length >= 4 && !linkedKeywords.has(key)) {
      targets.push({
        phrase: String(rawTag).trim(),
        href: `/mavzu/${slug}`,
        key,
      });
    }
  }

  if (targets.length === 0) return paragraph;

  // Uzunroq iboralarni birinchi tutish (masalan "Abduqodir Husanov" "Husanov" dan oldin)
  targets.sort((a, b) => b.phrase.length - a.phrase.length);

  const pattern = new RegExp(
    `(?<![\\w«"'])(?:«)?(${targets.map((t) => escapeRegex(t.phrase)).join("|")})(?:»)?(?![\\w»"'])`,
    "gi",
  );

  const elements = [];
  let lastIndex = 0;
  let match;

  while ((match = pattern.exec(paragraph)) !== null) {
    const matchText = match[1];
    const matchIndex = match.index;
    const target = targets.find(
      (t) => t.phrase.toLowerCase() === matchText.toLowerCase(),
    );

    if (!target || linkedKeywords.has(target.key)) {
      continue;
    }

    if (matchIndex > lastIndex) {
      elements.push(paragraph.slice(lastIndex, matchIndex));
    }

    elements.push(
      <Link
        key={`${target.href}-${matchIndex}`}
        href={target.href}
        className="font-semibold text-emerald-400 hover:text-emerald-300 underline underline-offset-4 decoration-emerald-500/40 hover:decoration-emerald-400 transition-colors"
      >
        {match[0]}
      </Link>,
    );

    linkedKeywords.add(target.key);
    lastIndex = matchIndex + match[0].length;
  }

  if (elements.length === 0) return paragraph;

  if (lastIndex < paragraph.length) {
    elements.push(paragraph.slice(lastIndex));
  }

  return elements;
}
