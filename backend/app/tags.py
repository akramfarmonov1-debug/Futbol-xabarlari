"""Teglarni yagona kanonik ko'rinishga keltirish.

Teglarni model har safar erkin yozadi, shuning uchun bitta jamoa yoki turnir
sayt bo'ylab bir necha ko'rinishda paydo bo'ladi: "Barsa" / "Barselona" /
"Barcelona", "Real" / "Реал". Trend ro'yxati ularni alohida sanaydi, o'xshash
xabarlar qidiruvi esa umumiy tegni topa olmaydi.

Teg ikki qismga ajratiladi:
  - kalit (`tag_key`) — solishtirish uchun; registr, apostrof va tinish
    belgilari hisobga olinmaydi;
  - ko'rinish (`canonical_tag`) — saytda chiqadigan yagona yozuv.
"""

import re

from .services.names_glossary import canonicalize_names

# Klub, futbolchi va turnir nomlari bu yerda TAKRORLANMAYDI. Ular
# `names_glossary` da, saytning yagona yozuv konvensiyasi bilan belgilangan
# (Chelsea -> Chelsi, PSG -> PSJ, Bayern -> Bavariya) va `canonical_tag` avval
# o'shani qo'llaydi. Ikkinchi ro'yxat tutish teg bilan maqola matnini
# qarama-qarshi qo'yardi: matnda "Chelsi", tegda "Chelsea".
#
# Bu yerda faqat lug'at qamramaydigan narsalar: kirill yozuvi, qisqartmalar va
# mavzu teglari. Kanonik yozuvning o'zi avtomatik qo'shiladi.
_ALIAS_GROUPS: dict[str, tuple[str, ...]] = {
    # Kirill variantlar — Sports.uz manbasi kirillchada keladi
    "Real Madrid": ("реал", "реал мадрид"),
    "Barselona": ("барселона",),
    "Chelsi": ("челси",),
    "Liverpul": ("ливерпуль",),
    "Arsenal": ("арсенал",),
    "Manchester Yunayted": ("манчестер юнайтед",),
    "Manchester Siti": ("манчестер сити",),
    "Bavariya": ("бавария",),
    "PSJ": ("псж",),
    "Yuventus": ("ювентус",),
    "Inter": ("интер",),
    "Milan": ("милан",),
    "Napoli": ("наполи",),
    # Qisqartmalar — lug'atda yo'q
    "Chempionlar ligasi": ("ucl", "cl", "лига чемпионов"),
    "Yevropa ligasi": ("europa league", "uel"),
    "Premyer-liga": ("apl", "epl", "angliya premyer ligasi", "премьер лига"),
    "Jahon chempionati": ("world cup", "jch", "jahon kubogi", "чемпионат мира"),
    "Yevro": ("euro", "yevropa chempionati"),
    "FIFA": (),
    "UEFA": (),
    "VAR": (),
    "EFL": (),
    # Mavzular
    "Transfer": ("transferlar", "transfer bozori", "трансфер"),
    "Jarohat": ("jarohatlar", "shikast", "травма"),
    "Murabbiy": ("bosh murabbiy", "murabbiylar"),
    "Shartnoma": ("shartnomalar", "kontrakt"),
    # O'zbekiston
    "O'zbekiston terma jamoasi": (
        "ozbekiston termasi", "terma jamoa", "ozbekiston milliy termasi",
        "uzbekistan", "сборная узбекистана",
    ),
    "O'zbekiston futboli": ("ozbekiston chempionati", "pfl"),
    "Legionerlar": ("legioner", "ozbek legionerlari"),
}

_APOSTROPHES = re.compile(r"['’ʼʻ`´]")
_NON_WORD = re.compile(r"[\W_]+", re.UNICODE)


def tag_key(tag: str) -> str:
    """Solishtirish kaliti: registr, apostrof va tinish belgilaridan xoli."""
    text = _APOSTROPHES.sub("", (tag or "").lower())
    return " ".join(_NON_WORD.sub(" ", text).split())


_ALIASES: dict[str, str] = {}
for _label, _variants in _ALIAS_GROUPS.items():
    _ALIASES[tag_key(_label)] = _label
    for _variant in _variants:
        _ALIASES[tag_key(_variant)] = _label


def _clean(tag: str) -> str:
    """Ortiqcha bo'shliq, boshidagi '#' va chetdagi tinish belgilarini oladi."""
    return " ".join((tag or "").strip().lstrip("#").strip(" .,:;!?-").split())


def _stable_case(tag: str) -> str:
    """Notanish teg uchun yozuv.

    Bu yerda teglarning ko'pchiligi atoqli ot — futbolchi, klub yoki turnir
    nomi. Shuning uchun modelning katta harflari saqlanadi: "Abduqodir
    Husanov" ni "Abduqodir husanov" ga aylantirish nomni buzadi. Faqat
    butunlay kichik harfda kelgan teg bosh harfi bilan kattalashtiriladi.

    Bir tushunchaning ikki yozuvi ("Yosh futbolchilar" va "Yosh Futbolchilar")
    bundan keyin ham qolishi mumkin. Ular `tag_key` bo'yicha baribir bitta
    guruhga tushadi; takrorlanadigan muhim nomlar esa `_ALIAS_GROUPS` da
    qat'iy belgilangan.
    """
    if any(character.isupper() for character in tag):
        return tag
    return tag[:1].upper() + tag[1:]


def canonical_tag(tag: str) -> str:
    """Bitta tegning saytda ko'rinadigan yagona yozuvi. Bo'sh teg uchun ''.

    Avval maqola matni bilan bir xil lug'at qo'llanadi (`canonicalize_names`),
    shuning uchun teg va matn hech qachon qarama-qarshi bo'lmaydi. Undan
    keyingina lug'at qamramaydigan variantlar (kirill, qisqartma, mavzu)
    tekshiriladi.
    """
    cleaned = _clean(tag)
    if not cleaned:
        return ""
    cleaned = _clean(canonicalize_names(cleaned))
    return _ALIASES.get(tag_key(cleaned)) or _stable_case(cleaned)


def normalize_tags(tags, limit: int = 6) -> list[str]:
    """Teglar ro'yxatini kanonik ko'rinishga keltiradi va takrorlarini oladi.

    Chegara takrorlar tashlangandan keyin qo'llanadi — aks holda "Barsa" va
    "Barcelona" bitta o'rin o'rniga ikkitasini egallardi.
    """
    result: list[str] = []
    seen: set[str] = set()
    for tag in tags or []:
        canonical = canonical_tag(str(tag))
        if not canonical:
            continue
        key = tag_key(canonical)
        if key in seen:
            continue
        seen.add(key)
        result.append(canonical)
    return result[:limit]
