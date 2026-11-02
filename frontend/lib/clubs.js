/**
 * O'zbekiston Superligasi jamoalari uchun lokal yuqori sifatli gerblar.
 * cdn.pfl.uz ba'zan sekin ishlashi yoki tashqi resurslarni bloklashi sababli
 * barcha Superliga klublari logotiplari frontend/public/clubs ichiga joylashtirilgan.
 */

const UZB_CLUBS = {
  neftchi: "/clubs/neftchi.png",
  paxtakor: "/clubs/paxtakor.png",
  pakhtakor: "/clubs/paxtakor.png",
  navbahor: "/clubs/navbahor.png",
  okmk: "/clubs/okmk.png",
  agmk: "/clubs/okmk.png",
  nasaf: "/clubs/nasaf.png",
  buxoro: "/clubs/buxoro.png",
  bukhara: "/clubs/buxoro.png",
  lokomotiv: "/clubs/lokomotiv.png",
  qizilqum: "/clubs/qizilqum.png",
  dinamo: "/clubs/dinamo.png",
  andijon: "/clubs/andijon.png",
  andijan: "/clubs/andijon.png",
  "so'g'diyona": "/clubs/sogdiyona.png",
  "so‘g‘diyona": "/clubs/sogdiyona.png",
  sogdiyona: "/clubs/sogdiyona.png",
  sogdiana: "/clubs/sogdiyona.png",
  surxon: "/clubs/surxon.png",
  surkhon: "/clubs/surxon.png",
  bunyodkor: "/clubs/bunyodkor.png",
  "qo'qon-1912": "/clubs/qoqon-1912.png",
  "qo‘qon-1912": "/clubs/qoqon-1912.png",
  "qo'qon": "/clubs/qoqon-1912.png",
  qoqon: "/clubs/qoqon-1912.png",
  kokand: "/clubs/qoqon-1912.png",
  xorazm: "/clubs/xorazm.png",
  khorezm: "/clubs/xorazm.png",
  mashal: "/clubs/mashal.png",
  "mash'al": "/clubs/mashal.png",
  "mash‘al": "/clubs/mashal.png",
  metallurg: "/clubs/metallurg.png",
  olimpik: "/clubs/olimpik.png",
  olympic: "/clubs/olimpik.png",
};

export function getClubLogo(teamName, defaultCrest) {
  if (!teamName) return defaultCrest;
  const key = teamName.toLowerCase().trim();
  if (UZB_CLUBS[key]) return UZB_CLUBS[key];

  for (const [name, path] of Object.entries(UZB_CLUBS)) {
    if (key.includes(name) || name.includes(key)) {
      return path;
    }
  }

  return defaultCrest;
}
