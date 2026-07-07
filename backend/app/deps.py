from fastapi import Header, HTTPException

from .config import ADMIN_TOKEN


def require_admin(x_admin_token: str = Header(default="")):
    if not ADMIN_TOKEN or x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Admin token noto'g'ri")
