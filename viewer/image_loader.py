"""
Загрузка и кеширование картинок для viewer-а.
Без зависимости от tkinter — можно использовать из тестов.
"""
import hashlib
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

REQUEST_TIMEOUT = 15

SIZE_TYPES = ("bet_33", "bet_50", "bet_75", "bet_100")
ACTION_TYPES = ("fold", "check", "call", "bet", "raise")


def _cache_path(url):
    return CACHE_DIR / (hashlib.md5(url.encode()).hexdigest() + ".bin")


def load_image(url):
    """Скачать картинку (с кешем) и вернуть PIL.Image."""
    cache_file = _cache_path(url)
    if cache_file.exists():
        try:
            return Image.open(cache_file).copy()
        except Exception:
            cache_file.unlink(missing_ok=True)

    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    cache_file.write_bytes(resp.content)
    return Image.open(BytesIO(resp.content)).copy()
