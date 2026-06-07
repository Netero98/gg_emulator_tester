"""
Загрузка и кеширование картинок для viewer-а.
Без зависимости от tkinter — можно использовать из тестов.

Поддерживает:
  - HTTP/HTTPS URL (https://..., http://...)
  - file:// URL (file:///absolute/path/to/image.png)
  - абсолютные пути (/home/user/photos/image.png)
  - относительные пути (../photos/image.png) — резолвятся относительно scenarios.js
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


def _is_http_url(url: str) -> bool:
    return url.startswith(("http://", "https://"))


def _normalize_file_url(url: str) -> Path:
    """file:///path → Path, или просто путь."""
    if url.startswith("file://"):
        # file:///home/user/x.png → /home/user/x.png
        return Path(url[len("file://"):])
    return Path(url)


def load_image(url):
    """Скачать/прочитать картинку (с кешем) и вернуть PIL.Image.

    Поддерживает http(s)://, file://, абсолютные и относительные пути.
    Кеширование по MD5(url) — одинаковый URL не качается дважды.
    """
    cache_file = _cache_path(url)
    if cache_file.exists():
        try:
            return Image.open(cache_file).copy()
        except Exception:
            cache_file.unlink(missing_ok=True)

    if _is_http_url(url):
        # Сетевой URL — качаем через requests
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        cache_file.write_bytes(resp.content)
        return Image.open(BytesIO(resp.content)).copy()

    # Локальный файл (file:// или путь)
    path = _normalize_file_url(url)
    if not path.exists():
        # Попробуем разрешить относительный путь от scenarios.js
        resolved = _resolve_relative(path)
        if resolved is not None:
            path = resolved
    if not path.exists():
        raise FileNotFoundError(
            f"Image file not found: {url}\n"
            f"  tried: {path}\n"
            f"  (для локальных картинок укажите абсолютный путь или file:// URL)"
        )
    img = Image.open(path).copy()
    # Кешируем байты для консистентности
    try:
        with BytesIO() as buf:
            img.save(buf, format=img.format or "PNG")
            cache_file.write_bytes(buf.getvalue())
    except Exception:
        pass  # не критично — просто не кешируем
    return img


# Реестр базовых директорий для относительных путей.
# scenario_loader регистрирует сюда путь к scenarios.js при загрузке.
_BASE_DIRS = []


def register_base_dir(path: Path):
    """Зарегистрировать базовую директорию для резолва относительных путей.
    Вызывается из scenario_loader.parse_scenarios_js()."""
    p = Path(path).resolve()
    if p.is_dir():
        _BASE_DIRS.append(p)
    else:
        # Если передали путь к файлу — берём родителя
        parent = p.parent.resolve()
        if parent not in _BASE_DIRS:
            _BASE_DIRS.append(parent)


def _resolve_relative(path: Path) -> Path | None:
    """Попытаться разрешить относительный путь относительно зарегистрированных баз."""
    if path.is_absolute():
        return path if path.exists() else None
    for base in _BASE_DIRS:
        candidate = (base / path).resolve()
        if candidate.exists():
            return candidate
    return None
