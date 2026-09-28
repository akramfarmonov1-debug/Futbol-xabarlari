import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";

// Next 16'da `next build` lint qilmaydi — tekshiruv CI'da `npm run lint` bilan.
export default defineConfig([
  ...nextVitals,
  {
    rules: {
      // O'zbek matnida apostrof alifboning qismi (o', g') va React uni xavfsiz
      // chiqaradi. Qoida faqat JSX'da adashib qolgan ">" va "}" ni ushlasin.
      "react/no-unescaped-entities": ["error", { forbid: [">", "}"] }],
    },
  },
  globalIgnores([".next/**", "out/**", "node_modules/**"]),
]);
