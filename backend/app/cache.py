"""Qisqa muddatli xotira keshi.

Bir xil ro'yxat (bosh sahifa, kategoriya, sitemap) har bir sahifa ko'rilishida
bazadan qayta o'qilmasin: baza Neon'da va bepul tarif oyiga 5 GB trafik
beradi. Keshga faqat sessiyadan ajralgan qiymatlar (Pydantic modellar, oddiy
ma'lumot) qo'yiladi — ORM obyektlari sessiya yopilgach ishlamaydi.
"""

import time

_MAX_ENTRIES = 1000
_entries: dict[tuple, tuple[float, object]] = {}


def cached(key: tuple, ttl: float, producer):
    now = time.monotonic()
    hit = _entries.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1]
    value = producer()
    if len(_entries) >= _MAX_ENTRIES:
        # Crawler minglab turli slug so'rasa ham xotira cheksiz o'smasin.
        _entries.clear()
    _entries[key] = (now, value)
    return value


def clear() -> None:
    _entries.clear()
