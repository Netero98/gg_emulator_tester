"""
Сканер директории с фотками → JSON manifest.

Использование:
    python3 viewer/generate_manifest.py [PHOTOS_DIR] [OUTPUT_JSON]
По умолчанию:
    PHOTOS_DIR = docs/photos
    OUTPUT_JSON = docs/photos.json

Формат manifest:
    {
      "generated": "2024-...",
      "count": N,
      "photos_dir": "docs/photos",
      "photos": [
        {
          "rel": "photos/AKs_1_preflop.png",   # путь относительно docs/ (для scenarios.js)
          "name": "AKs_1_preflop.png",          # имя для отображения
          "subdir": "AKs",                       # подпапка (если есть)
          "size_bytes": 2452159
        },
        ...
      ]
    }

Пути в "rel" — относительно docs/, потому что:
  - configurator.html в docs/ → превью через <img src="photos/...">
  - scenarios.js в docs/js/ → для Python viewer резолвится через register_base_dir
  - web index.html в docs/ → работает с GitHub Pages (docs/ = корень)
"""
import json
import sys
import time
from pathlib import Path


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}


def scan(photos_dir: Path, docs_dir: Path) -> list[dict]:
    """Рекурсивно сканирует photos_dir, возвращает список фото."""
    photos = []
    if not photos_dir.exists():
        return photos
    for path in sorted(photos_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in IMAGE_EXTS:
            continue
        # rel path относительно docs/, например "photos/AKs/1.png"
        rel = path.relative_to(docs_dir).as_posix()
        # подпапка (родитель относительно photos_dir), пустая строка если корень
        try:
            subdir = path.parent.relative_to(photos_dir).as_posix()
            if subdir == ".":
                subdir = ""
        except ValueError:
            subdir = ""
        photos.append({
            "rel": rel,
            "name": path.name,
            "subdir": subdir,
            "size_bytes": path.stat().st_size,
        })
    return photos


def main(argv: list[str]) -> int:
    here = Path(__file__).parent
    repo = here.parent
    photos_dir = Path(argv[1]) if len(argv) > 1 else repo / "docs" / "photos"
    output = Path(argv[2]) if len(argv) > 2 else repo / "docs" / "photos.json"
    # docs_dir = директория manifest'а (всё относительно неё: photos/*, photos.json)
    docs_dir = output.parent

    if not photos_dir.exists():
        print(f"✗ Директория {photos_dir} не существует", file=sys.stderr)
        return 1

    photos = scan(photos_dir, docs_dir)
    manifest = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "count": len(photos),
        "photos_dir": str(photos_dir.relative_to(docs_dir)),
        "photos": photos,
    }
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ {len(photos)} фото → {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
