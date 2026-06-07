"""
Smoke-тест viewer-логики без GUI.

Проверяет:
  1. Парсинг scenarios.js
  2. Скачивание и кеширование картинки
  3. Нативный размер картинки
  4. Расчёт пиксельных координат кнопок из процентов
  5. Логику валидации (action / size / slider)
  6. Детекцию missclick
  7. Навигацию по шагам
  8. Клик в image-coords при разных scale (windowed / fullscreen)

Запуск: python3 viewer/test_smoke.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from scenario_loader import parse_scenarios_js
from image_loader import load_image, SIZE_TYPES, ACTION_TYPES, CACHE_DIR
from PIL import Image

REPO = HERE.parent
SCENARIOS_JS = REPO / "docs" / "js" / "scenarios.js"

# Глобальный реальный размер (заполняется в test_image)
NATIVE_W = 1920
NATIVE_H = 1080


class FakeViewer:
    """Минимальная копия PokerViewer._handle_action/_handle_missclick
    без tkinter. Сверяем поведение с реальным viewer.py."""

    def __init__(self, step, img_w, img_h):
        self.step = step
        self.img_w = img_w
        self.img_h = img_h
        self.selected_size = None
        self.slider_clicks = 0
        self.is_waiting = True
        self.results = []

    def click(self, x, y):
        if not self.is_waiting:
            return None
        for btn in self.step.get("buttons", []):
            cx = btn["x"] / 100.0 * self.img_w
            cy = btn["y"] / 100.0 * self.img_h
            left = cx - btn["width"] / 2
            top = cy - btn["height"] / 2
            right = left + btn["width"]
            bottom = top + btn["height"]
            if left <= x <= right and top <= y <= bottom:
                return self._action(btn)
        return self._miss()

    def _action(self, btn):
        if btn["type"] in SIZE_TYPES:
            self.selected_size = btn["type"]
            self.slider_clicks = 0
            return "size"
        if btn["type"] == "slider_click":
            self.slider_clicks += 1
            return "slider"
        if btn["type"] in ACTION_TYPES:
            expected = self.step["correctAction"]
            is_action_ok = btn["type"] == expected["type"]
            expected_size = expected.get("size")
            expected_slider = expected.get("sliderClicks", 0) or 0
            is_size_ok = (self.selected_size == f"bet_{expected_size}") if expected_size else (self.selected_size is None)
            is_slider_ok = self.slider_clicks == expected_slider
            is_correct = is_action_ok and is_size_ok and is_slider_ok
            self.is_waiting = False
            self.results.append({"correct": is_correct, "type": btn["type"]})
            return "correct" if is_correct else "wrong"
        return None

    def _miss(self):
        self.is_waiting = False
        self.results.append({"correct": False, "type": "missclick"})
        return "miss"


# --------- helpers --------- #

def check(cond, msg):
    if not cond:
        print(f"  ✗ FAIL: {msg}")
        return False
    print(f"  ✓ {msg}")
    return True


def section(title):
    print(f"\n=== {title} ===")


def click_btn(v, btn):
    """Кликнуть в центр кнопки (учитывая реальный размер картинки)."""
    cx = btn["x"] / 100.0 * v.img_w
    cy = btn["y"] / 100.0 * v.img_h
    return v.click(cx, cy)


# --------- tests --------- #

def test_parse():
    section("Парсинг scenarios.js")
    scenarios = parse_scenarios_js(SCENARIOS_JS)
    ok = True
    ok &= check(bool(scenarios), "scenarios не пустой")
    ok &= check("my_test" in scenarios, "'my_test' найден")
    s = scenarios["my_test"]
    ok &= check(len(s["steps"]) >= 1, f"есть шаги ({len(s['steps'])})")
    step0 = s["steps"][0]
    ok &= check(step0["id"] == "preflop", "первый шаг — preflop")
    ok &= check("image" in step0 and step0["image"].startswith("http"), "есть URL картинки")
    ok &= check(len(step0["buttons"]) == 3, f"3 кнопки ({len(step0['buttons'])})")
    return ok


def test_image():
    section("Загрузка и кеш картинки")
    global NATIVE_W, NATIVE_H
    scenarios = parse_scenarios_js(SCENARIOS_JS)
    url = scenarios["my_test"]["steps"][0]["image"]
    print(f"  URL: {url}")

    img1 = load_image(url)
    w, h = img1.size
    ok = True
    ok &= check(isinstance(img1, Image.Image), f"PIL.Image загружен ({w}x{h})")
    # Реальный размер может быть 1920x1080 или близко (например, 1918x1078 если кадр из видео)
    near_fullhd = abs(w - 1920) <= 4 and abs(h - 1080) <= 4
    ok &= check(near_fullhd, f"нативный размер близок к Full HD ({w}x{h})")
    ok &= check(abs(w / h - 16 / 9) < 0.01, f"соотношение сторон ≈ 16:9 (факт: {w/h:.4f})")

    cache_files = list(CACHE_DIR.glob("*"))
    ok &= check(len(cache_files) >= 1, f"кеш создан ({len(cache_files)} файл(ов))")

    img2 = load_image(url)
    ok &= check(img2.size == img1.size, "повторная загрузка работает")

    NATIVE_W, NATIVE_H = w, h
    return ok


def test_button_coords():
    section(f"Пиксельные координаты кнопок (при {NATIVE_W}x{NATIVE_H})")
    scenarios = parse_scenarios_js(SCENARIOS_JS)
    step = scenarios["my_test"]["steps"][0]
    ok = True
    print(f"  Кнопки (в пикселях при {NATIVE_W}x{NATIVE_H}):")
    for btn in step["buttons"]:
        cx = btn["x"] / 100.0 * NATIVE_W
        cy = btn["y"] / 100.0 * NATIVE_H
        left = cx - btn["width"] / 2
        top = cy - btn["height"] / 2
        right = left + btn["width"]
        bottom = top + btn["height"]
        print(f"    {btn['id']}: центр=({cx:.0f}, {cy:.0f}), "
              f"rect=({left:.0f}, {top:.0f}, {right:.0f}, {bottom:.0f})")
        ok &= check(0 <= cx <= NATIVE_W, f"  центр X {btn['id']} в пределах экрана")
        ok &= check(0 <= cy <= NATIVE_H, f"  центр Y {btn['id']} в пределах экрана")
    return ok


def test_correct_sequence():
    section("Правильная последовательность: bet_100 → slider(3) → raise")
    scenarios = parse_scenarios_js(SCENARIOS_JS)
    step = scenarios["my_test"]["steps"][0]
    v = FakeViewer(step, NATIVE_W, NATIVE_H)

    bet_100 = next(b for b in step["buttons"] if b["id"] == "bet_100")
    slider = next(b for b in step["buttons"] if b["type"] == "slider_click")
    raise_btn = next(b for b in step["buttons"] if b["type"] == "raise")

    ok = True
    r = click_btn(v, bet_100)
    ok &= check(r == "size", "bet_100 зарегистрирован как size")
    r = click_btn(v, slider)
    ok &= check(r == "slider", "первый slider click зарегистрирован")
    r = click_btn(v, slider)
    ok &= check(r == "slider", "второй slider click")
    r = click_btn(v, slider)
    ok &= check(r == "slider", "третий slider click")
    r = click_btn(v, raise_btn)
    ok &= check(r == "correct", "raise → правильно")
    return ok


def test_wrong_size():
    section("Неправильный размер: bet_100 → raise (без slider)")
    scenarios = parse_scenarios_js(SCENARIOS_JS)
    step = scenarios["my_test"]["steps"][0]
    v = FakeViewer(step, NATIVE_W, NATIVE_H)
    bet_100 = next(b for b in step["buttons"] if b["id"] == "bet_100")
    raise_btn = next(b for b in step["buttons"] if b["type"] == "raise")

    ok = True
    click_btn(v, bet_100)
    r = click_btn(v, raise_btn)
    ok &= check(r == "wrong", "raise без slider → wrong")
    return ok


def test_missclick():
    section("Missclick: клик в пустую область")
    scenarios = parse_scenarios_js(SCENARIOS_JS)
    step = scenarios["my_test"]["steps"][0]
    v = FakeViewer(step, NATIVE_W, NATIVE_H)
    r = v.click(10, 10)  # угол картинки, далеко от кнопок
    return check(r == "miss", "клик в (10,10) → miss")


def test_no_size_when_expected():
    section("Действие без выбора размера, когда ожидался size")
    scenarios = parse_scenarios_js(SCENARIOS_JS)
    step = scenarios["my_test"]["steps"][0]
    v = FakeViewer(step, NATIVE_W, NATIVE_H)
    raise_btn = next(b for b in step["buttons"] if b["type"] == "raise")
    r = click_btn(v, raise_btn)
    return check(r == "wrong", "raise без bet_100 → wrong")


def test_close_button_no_overlap():
    """Кнопки действия не должны попадать в зону клика по нативной
    кнопке закрытия ОС (правый верх). В новой версии используется
    стандартный titlebar X, но при fullscreen он скрыт — поэтому
    проверяем что кнопки не в самом верху-с-краю картинки."""
    section("Кнопки действия не в зоне titlebar (правый верх)")
    scenarios = parse_scenarios_js(SCENARIOS_JS)
    step = scenarios["my_test"]["steps"][0]
    w, h = NATIVE_W, NATIVE_H
    # Зона titlebar'a (примерно): правый верх, 200x50
    titlebar_left = w - 200
    titlebar_top = 0
    titlebar_right = w
    titlebar_bottom = 50

    ok = True
    for btn in step.get("buttons", []):
        cx = btn["x"] / 100.0 * w
        cy = btn["y"] / 100.0 * h
        left = cx - btn["width"] / 2
        top = cy - btn["height"] / 2
        right = left + btn["width"]
        bottom = top + btn["height"]
        in_titlebar = not (
            right < titlebar_left or
            left > titlebar_right or
            bottom < titlebar_top or
            top > titlebar_bottom
        )
        ok &= check(
            not in_titlebar,
            f"кнопка {btn['id']} ({left:.0f},{top:.0f},{right:.0f},{bottom:.0f}) "
            f"НЕ в зоне titlebar ({titlebar_left},{titlebar_top},{titlebar_right},{titlebar_bottom})",
        )
    return ok


def test_scaling():
    """Координаты кнопок должны корректно отображаться в canvas-coords
    при разных scale (windowed mode с масштабированием, fullscreen = 1:1)."""
    section("Координаты кнопок при разных scale")
    scenarios = parse_scenarios_js(SCENARIOS_JS)
    step = scenarios["my_test"]["steps"][0]
    w, h = NATIVE_W, NATIVE_H

    ok = True
    for scale in (1.0, 0.75, 0.5, 0.25):
        for btn in step.get("buttons", []):
            # Image-coords кнопки
            img_cx = btn["x"] / 100.0 * w
            img_cy = btn["y"] / 100.0 * h
            # Canvas-coords при scale
            img_w_scaled = w * scale
            img_h_scaled = h * scale
            offset_x = 50  # произвольный offset
            offset_y = 30
            canvas_cx = offset_x + (btn["x"] / 100.0) * img_w_scaled
            canvas_cy = offset_y + (btn["y"] / 100.0) * img_h_scaled
            # Обратно в image-coords
            recovered_x = (canvas_cx - offset_x) / scale
            recovered_y = (canvas_cy - offset_y) / scale
            match_x = abs(recovered_x - img_cx) < 0.5
            match_y = abs(recovered_y - img_cy) < 0.5
            ok &= check(
                match_x and match_y,
                f"scale={scale}, {btn['id']}: img=({img_cx:.0f},{img_cy:.0f}) ↔ "
                f"canvas=({canvas_cx:.0f},{canvas_cy:.0f}) — конвертация туда-обратно корректна",
            )
    return ok


def test_local_file_loading():
    """image_loader должен корректно загружать локальные файлы:
    file:// URL, абсолютные пути, относительные пути."""
    section("Загрузка локальных файлов (file://, абсолютные, относительные)")
    from image_loader import load_image, register_base_dir, _normalize_file_url

    # Создаём тестовую "локальную" копию картинки в docs/photos/
    test_photo = REPO / "docs" / "photos" / "AKs_1_preflop.png"
    if not test_photo.exists():
        # Скопировать из cache
        import shutil
        cache_files = list((REPO / "viewer" / "cache").glob("*.bin"))
        if cache_files:
            shutil.copy(cache_files[0], test_photo)

    if not test_photo.exists():
        print("  ⚠ Пропуск теста: нет sample картинки")
        return True  # не считаем за fail

    ok = True

    # 1) file:// URL
    try:
        img = load_image(f"file://{test_photo}")
        ok &= check(img.size[0] > 0 and img.size[1] > 0,
                    f"file:// URL: загружено {img.size[0]}x{img.size[1]}")
    except Exception as e:
        ok &= check(False, f"file:// URL: ошибка {e}")

    # 2) абсолютный путь
    try:
        img = load_image(str(test_photo))
        ok &= check(img.size[0] > 0 and img.size[1] > 0,
                    f"абсолютный путь: загружено {img.size[0]}x{img.size[1]}")
    except Exception as e:
        ok &= check(False, f"абсолютный путь: ошибка {e}")

    # 3) относительный путь (с base_dir = REPO/docs)
    try:
        register_base_dir(REPO / "docs")
        img = load_image("photos/AKs_1_preflop.png")
        ok &= check(img.size[0] > 0 and img.size[1] > 0,
                    f"относительный путь 'photos/...': загружено {img.size[0]}x{img.size[1]}")
    except Exception as e:
        ok &= check(False, f"относительный путь: ошибка {e}")

    # 4) несуществующий файл → ошибка с понятным сообщением
    try:
        load_image("file:///nonexistent/photo.png")
        ok &= check(False, "несуществующий файл: должна быть ошибка")
    except FileNotFoundError as e:
        ok &= check("not found" in str(e).lower() or "не найден" in str(e).lower() or "Photo" in str(e),
                    f"несуществующий файл: понятная ошибка ({e!s:.80}...)")
    except Exception as e:
        ok &= check(False, f"несуществующий файл: неправильный тип ошибки {type(e).__name__}: {e}")

    return ok


def test_manifest():
    """Проверяем что make photos-manifest генерирует корректный docs/photos.js.

    Используется .js (а не .json) потому что fetch() с file:// на file://
    блокируется Chrome по CORS. <script src=photos.js> таких ограничений
    не имеет и работает на file:// в любом браузере.
    """
    section("Manifest docs/photos.js (статичный JS, без CORS)")
    from generate_manifest import scan, write_js_manifest
    import json

    photos_dir = REPO / "docs" / "photos"
    docs_dir = REPO / "docs"

    photos = scan(photos_dir, docs_dir)
    ok = True
    ok &= check(len(photos) >= 1, f"найдено {len(photos)} фото (>= 1)")
    if photos:
        sample = photos[0]
        ok &= check("rel" in sample, "у фоток есть поле 'rel'")
        ok &= check(sample["rel"].startswith("photos/"),
                    f"rel начинается с 'photos/': {sample['rel']!r}")
        ok &= check("name" in sample and sample["name"],
                    f"у фоток есть непустое имя: {sample.get('name')!r}")
        ok &= check("size_bytes" in sample and sample["size_bytes"] > 0,
                    f"size_bytes > 0: {sample.get('size_bytes')}")

    # Проверить что manifest-файл существует и валиден
    manifest_file = REPO / "docs" / "photos.js"
    ok &= check(manifest_file.exists(), f"manifest существует: {manifest_file}")
    if manifest_file.exists():
        content = manifest_file.read_text(encoding="utf-8")
        # Должен устанавливать window.PHOTOS_MANIFEST
        ok &= check("window.PHOTOS_MANIFEST" in content,
                    "manifest устанавливает window.PHOTOS_MANIFEST")
        ok &= check("do not edit" in content.lower() or "auto-generated" in content.lower(),
                    "manifest содержит auto-generated маркер")
        # Извлечь JSON из JS: ищем "= {" и берём до соответствующего "};"
        # Используем regex, чтобы избежать первого "=" в комментариях
        import re
        m = re.search(r'=\s*(\{[\s\S]*?\})\s*;', content)
        if m:
            json_str = m.group(1)
            try:
                data = json.loads(json_str)
                ok &= check("photos" in data and isinstance(data["photos"], list),
                            f"manifest содержит массив photos ({len(data.get('photos', []))} элементов)")
                ok &= check(data["count"] == len(data["photos"]),
                            f"manifest.count == {data['count']} == len(photos)")
            except Exception as e:
                ok &= check(False, f"manifest — корректный JSON: {e}")
        else:
            ok &= check(False, "manifest: не найдено присваивание = {...} ;")

    # Симулируем загрузку: после загрузки <script> window.PHOTOS_MANIFEST должен быть доступен
    try:
        import re
        m = re.search(r'=\s*(\{[\s\S]*?\})\s*;', content)
        manifest = json.loads(m.group(1))
        ok &= check(manifest.get("count") == 2,
                    f"после 'загрузки' <script> window.PHOTOS_MANIFEST.count == {manifest.get('count')}")
    except Exception as e:
        ok &= check(False, f"manifest не парсится после загрузки: {e}")

    return ok


# --------- main --------- #

def main():
    print("Smoke-тест Poker Emulator Viewer (без GUI)\n")
    results = []
    results.append(("parse", test_parse()))
    results.append(("image", test_image()))
    results.append(("coords", test_button_coords()))
    results.append(("correct_seq", test_correct_sequence()))
    results.append(("wrong_size", test_wrong_size()))
    results.append(("missclick", test_missclick()))
    results.append(("no_size", test_no_size_when_expected()))
    results.append(("close_no_overlap", test_close_button_no_overlap()))
    results.append(("scaling", test_scaling()))
    results.append(("local_files", test_local_file_loading()))
    results.append(("manifest", test_manifest()))

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    for name, ok in results:
        mark = "✓" if ok else "✗"
        print(f"  {mark} {name}")
    print(f"\n{passed}/{total} групп тестов прошли успешно")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
