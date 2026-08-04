"""O'zbekcha futbol nomlari lug'ati.

Klub, futbolchi va turnir nomlarining o'zbek matbuotida qabul qilingan yagona
yozilishini ta'minlaydi. AI matnida yoki RSS'da turli transkripsiyada kelgan
nomlar kanonik shaklga keltiriladi.

Qo'llanish::

    from .names_glossary import canonicalize_names
    text = canonicalize_names("Chelsea Wrexhamga qarshi")

Kanonik shakl o'zbek lotin matbuotidagi qabul qilingan yozilishdir
(masalan: Chelsea → Chelsi, Wrexham → Vrekshem, Rangers → Reynjers).
"""

import re

# (variant, kanonik) juftliklari — word-boundary va katta-kichik harf farqiga
# chidamli. Kanonik shakl har doim lotin o'zbek yozuvida.
_GLOSSARY: list[tuple[re.Pattern, str]] = []


def _add(variants: tuple[str, ...], canonical: str) -> None:
    """Berilgan variantlarni kanonik shaklga o'giradigan regex ro'yxatga qo'shadi."""
    pattern = re.compile(
        r"(?<![A-Za-zÀ-žʻʼ'])("
        + "|".join(re.escape(variant) for variant in variants)
        + r")(?![A-Za-zÀ-žʻʼ'])",
        re.IGNORECASE,
    )
    _GLOSSARY.append((pattern, canonical))


# --- Klublar / jamoalar ---
_add(("Chelsea",), "Chelsi")
_add(("Liverpool",), "Liverpul")
_add(("Barcelona", "Barselon"), "Barselona")
_add(("Rangers", "Rencers", "Renjers"), "Reynjers")
_add(("Wrexham", "Vreksham"), "Vrekshem")
_add(("Newcastle", "Nyukasl", "Nyu-kasl"), "Nyukasl")
_add(("Leicester",), "Lester")
_add(("Nottingham Forest", "Nottingem Forest"), "Nottingem Forest")
_add(("Bournemouth", "Bornmut"), "Bornmut")
_add(("Wolverhampton", "Vulverxempton", "Vulves"), "Vulverxempton")
_add(("West Ham", "Vest Hem"), "Vest Hem")
_add(("Leeds",), "Lids")
_add(("Atletico Madrid", "Atlético Madrid"), "Atletiko Madrid")
_add(("Atletico", "Atlético"), "Atletiko")
_add(("Juventus", "Yuventus"), "Yuventus")
_add(("Bayern Munich", "Bayern Myunxen", "Bavariya Myunxen"), "Bavariya")
_add(("Borussia Dortmund", "Borussiya Dortmund"), "Borussiya Dortmund")
_add(("Paris Saint-Germain", "Parij Sen-Jermen", "Parij Sen-Jermain"), "Parij Sen-Jermen")
_add(("Celtic", "Seltik"), "Seltik")
_add(("Strasbourg", "Strasburg"), "Strasburg")
_add(("Stuttgart", "Shtutgart"), "Shtutgart")
_add(("Manchester City", "Manchester Siti"), "Manchester Siti")
_add(("Manchester United", "Manchester Yunayted"), "Manchester Yunayted")
_add(("Tottenham",), "Tottenham")
_add(("Everton",), "Everton")
_add(("Aston Villa",), "Aston Villa")

# --- Futbolchilar ---
_add(("Mohamed Salah", "Mohammad Salah", "Muhammad Saloh", "Mohamed Soloh"), "Mohamed Soloh")
_add(("Erling Haaland", "Erling Xoland"), "Erling Xoland")
_add(("Kylian Mbappe", "Kilian Mbappe"), "Kilian Mbappe")
_add(("Vinicius Junior", "Vinisius Junior", "Vinisius"), "Vinisius Junior")
_add(("Jude Bellingham", "Jude Bellingem"), "Jude Bellingem")
_add(("Harry Kane", "Garri Keyn"), "Garri Keyn")
_add(("Valentin Barco", "Valetin Barko", "Valentin Barko"), "Valentin Barko")
_add(("Abdukodir Khusanov", "Abduqodir Xusanov", "Abduqodir Husanov"), "Abduqodir Husanov")

# --- Keng tarqalgan so'z variantlarini birxillashtirish ---
_add(("muxokama",), "muhokama")
_add(("muallif",), "muallif")  # saqlab qolish uchun no-op qator
_add(("premer-liga", "premyer-liga"), "Premyer-liga")
_add(("champions liga", "chempionlar liga"), "Chempionlar ligasi")


def canonicalize_names(text: str | None) -> str:
    """Matndagi nomlarni kanonik o'zbekcha yozilishga keltiradi."""
    result = str(text or "")
    for pattern, canonical in _GLOSSARY:
        result = pattern.sub(canonical, result)
    return result
