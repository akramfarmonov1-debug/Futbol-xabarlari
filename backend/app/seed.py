from sqlalchemy.orm import Session

from .models import Category

# TZ bo'yicha kategoriyalar
CATEGORIES = [
    ("Transferlar", "transferlar"),
    ("Premyer-liga", "premyer-liga"),
    ("La Liga", "la-liga"),
    ("Seriya A", "seriya-a"),
    ("Bundesliga", "bundesliga"),
    ("Chempionlar ligasi", "chempionlar-ligasi"),
    ("Jahon futboli", "jahon-futboli"),
    ("O'zbekiston futboli", "uzbekiston-futboli"),
    ("Terma jamoalar", "terma-jamoalar"),
]


def seed_categories(db: Session) -> None:
    existing = {slug for (slug,) in db.query(Category.slug).all()}
    for name, slug in CATEGORIES:
        if slug not in existing:
            db.add(Category(name=name, slug=slug))
    db.commit()
