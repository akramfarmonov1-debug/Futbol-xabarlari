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
_add(("Real Madrid", "Real-Madrid"), "Real Madrid")
_add(("Internazionale", "Inter Milan", "Inter"), "Inter")
_add(("AC Milan", "A.C. Milan"), "Milan")
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
_add(("Napoli",), "Napoli")
_add(("Roma", "AS Roma"), "Roma")
_add(("Lazio", "Latsio"), "Latsio")
_add(("Bayern Munich", "Bayern Myunxen", "Bavariya Myunxen", "Bayern"), "Bavariya")
_add(("Borussia Dortmund", "Borussiya Dortmund", "Dortmund"), "Borussiya Dortmund")
_add(("Bayer Leverkusen", "Bayer", "Leverkusen"), "Bayer Leverkuzen")
_add(("RB Leipzig", "Leipzig", "Leyptsig"), "RB Leyptsig")
_add(("Paris Saint-Germain", "Parij Sen-Jermen", "Parij Sen-Jermain", "PSG"), "PSJ")
_add(("Monaco", "Monako"), "Monako")
_add(("Marseille", "Marsel"), "Marsel")
_add(("Celtic", "Seltik"), "Seltik")
_add(("Strasbourg", "Strasburg"), "Strasburg")
_add(("Stuttgart", "Shtutgart"), "Shtutgart")
_add(("Manchester City", "Manchester Siti"), "Manchester Siti")
_add(("Manchester United", "Manchester Yunayted"), "Manchester Yunayted")
_add(("Tottenham Hotspur", "Tottenham"), "Tottenxem")
_add(("Everton",), "Everton")
_add(("Aston Villa",), "Aston Villa")
_add(("Sporting CP", "Sporting Lisbon"), "Sporting")
_add(("Benfica", "Benfika"), "Benfika")
_add(("Porto", "Portu"), "Portu")
_add(("Galatasaray", "Galatasaroy"), "Galatasaroy")
_add(("Fenerbahce", "Fenerbaxche"), "Fenerbaxche")
_add(("Besiktas", "Beshiktosh"), "Beshiktosh")
_add(("Al-Hilal", "Al Hilal"), "Al-Hilol")
_add(("Al-Nassr", "Al Nassr"), "Al-Nassr")
_add(("Al-Ittihad", "Al Ittihad"), "Al-Ittihod")
_add(("Al-Ahli", "Al Ahli"), "Al-Ahli")

# --- Futbolchilar & Murabbiylar ---
_add(("Mohamed Salah", "Mohammad Salah", "Muhammad Saloh", "Mohamed Soloh"), "Muhammad Saloh")
_add(("Cristiano Ronaldo", "Krishtianu Ronaldo", "Krishtianu Ronaldu"), "Krishtianu Ronaldu")
_add(("Lionel Messi", "Leo Messi"), "Lionel Messi")
_add(("Erling Haaland", "Erling Xoland", "Erling Holand"), "Erling Xoland")
_add(("Kylian Mbappe", "Kilian Mbappe", "Kilían Mbappé"), "Kilian Mbappe")
_add(("Vinicius Junior", "Vinisius Junior", "Vinisius"), "Vinisius Junior")
_add(("Jude Bellingham", "Jude Bellingem"), "Jud Bellingem")
_add(("Harry Kane", "Garri Keyn"), "Harri Keyn")
_add(("Lamine Yamal", "Lamin Yamal"), "Lamin Yamal")
_add(("Bukayo Saka", "Bukayo Sako"), "Bukayo Saka")
_add(("Cole Palmer", "Koul Palmer"), "Koul Palmer")
_add(("Florian Wirtz", "Florian Virts"), "Florian Virts")
_add(("Jamal Musiala", "Jamol Musiala"), "Jamal Musiala")
_add(("Dani Olmo", "Dany Olmo"), "Dani Olmo")
_add(("Viktor Gyokeres", "Viktor Gyökeres", "Viktor Dokerash"), "Viktor Dyokeresh")
_add(("Valentin Barco", "Valetin Barko", "Valentin Barko"), "Valentin Barko")
_add(("Gianni Infantino", "Janni Infantino"), "Janni Infantino")
_add(("Carlo Ancelotti", "Karlo Anchelotti"), "Karlo Anchelotti")
_add(("Pep Guardiola", "Pep Gvardiola"), "Pep Gvardiola")
_add(("Mikel Arteta",), "Mikel Arteta")
_add(("Arne Slot",), "Arne Slot")

# --- O'zbekistonlik Futbolchilar & Murabbiylar ---
_add(("Abdukodir Khusanov", "Abduqodir Xusanov", "Abduqodir Husanov"), "Abduqodir Husanov")
_add(("Eldor Shomurodov", "Eldor Shomurodov"), "Eldor Shomurodov")
_add(("Abbosbek Fayzullaev", "Abbosbek Fayzullayev", "Abbos Fayzullaev"), "Abbosbek Fayzullayev")
_add(("Oston Urunov", "Oston O'runov", "Oston O‘runov"), "Oston O'runov")
_add(("Jaloliddin Masharipov", "Jaloliddin Masharipov"), "Jaloliddin Masharipov")
_add(("Husniddin Aliqulov", "Xusniddin Aliqulov"), "Husniddin Aliqulov")
_add(("Srecko Katanec", "Srechko Katanets"), "Srechko Katanets")

# --- Keng tarqalgan so'z variantlarini birxillashtirish ---
_add(("muxokama",), "muhokama")
_add(("muallif",), "muallif")
_add(("premer-liga", "premyer-liga", "premier league"), "Premyer-liga")
_add(("la-liga", "la liga"), "La Liga")
_add(("seriya-a", "serie a", "seriya a"), "Seriya A")
_add(("bundesliga", "bundes liga"), "Bundesliga")
_add(("champions liga", "chempionlar liga", "champions league"), "Chempionlar ligasi")
_add(("superliga", "super liga"), "Superliga")


def canonicalize_names(text: str | None) -> str:
    """Matndagi nomlarni kanonik o'zbekcha yozilishga keltiradi."""
    result = str(text or "")
    for pattern, canonical in _GLOSSARY:
        result = pattern.sub(canonical, result)
    return result
