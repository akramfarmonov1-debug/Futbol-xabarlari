"""Futbol Xabar — Telegram bot launcher.

Delegates to backend.app.bot.bot for unified bot execution and runtime lock.
"""
import asyncio
from pathlib import Path
import sys

# Ensure backend directory is in python path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.bot.bot import main  # noqa: E402

if __name__ == "__main__":
    asyncio.run(main())
