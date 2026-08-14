import hashlib
import re
import sys


def safe_print(*args, **kwargs) -> None:
    """Windows va no-UTF8 konsollarda UnicodeEncodeError bermasdan xavfsiz chop etadi."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "ascii"
        safe_args = [
            str(arg).encode(encoding, errors="replace").decode(encoding)
            for arg in args
        ]
        print(*safe_args, **kwargs)


def slugify(text: str) -> str:
    """O'zbek lotin matnidan URL uchun slug yasaydi."""
    text = text.lower().replace("'", "").replace("ʻ", "").replace("’", "")
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text).strip("-")
    return text[:200] or "maqola"


def title_hash(title: str) -> str:
    """Dublikatlarni aniqlash uchun normallashtirilgan sarlavha xeshi."""
    normalized = re.sub(r"[^a-z0-9]", "", title.lower())
    return hashlib.sha256(normalized.encode()).hexdigest()

