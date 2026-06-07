"""
Poker Emulator Viewer — десктопное приложение для нативного отображения
покерных скриншотов с валидацией действий.

Создаёт borderless окно точно по размеру картинки (1920x1080 для Full HD
скриншотов) в заданной позиции экрана, чтобы HDMI capture получил 1:1
копию исходного изображения без UI-обвязки браузера.

Запуск:
    python viewer.py --scenario my_test
    python viewer.py --scenario my_test --position 1920,0  # на втором мониторе
    python viewer.py --scenario my_test --no-topmost
"""
import argparse
import sys
import time
import tkinter as tk
from pathlib import Path

from PIL import ImageTk

try:
    from scenario_loader import parse_scenarios_js, list_scenarios
    from image_loader import load_image, CACHE_DIR, SIZE_TYPES, ACTION_TYPES
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from scenario_loader import parse_scenarios_js, list_scenarios
    from image_loader import load_image, CACHE_DIR, SIZE_TYPES, ACTION_TYPES


# ---------------------------- viewer ---------------------------- #

class PokerViewer:
    def __init__(self, root, scenarios, scenario_id, position=(0, 0),
                 topmost=True, debug=False, log_clicks=False):
        self.root = root
        self.scenarios = scenarios
        if scenario_id not in scenarios:
            ids = ", ".join(s[0] for s in list_scenarios(scenarios))
            raise ValueError(f"Scenario '{scenario_id}' not found. Available: {ids}")
        self.scenario_id = scenario_id
        self.scenario = scenarios[scenario_id]
        self.position = position
        self.topmost = topmost
        self.debug = debug
        self.log_clicks = log_clicks

        # runtime state
        self.step_idx = 0
        self.results = []
        self.selected_size = None
        self.slider_clicks = 0
        self.step_actions = []
        self.miss_clicks = 0
        self.is_waiting = True
        self.img_w = 0
        self.img_h = 0
        self.tk_img = None
        self.canvas = None
        self.click_log_path = None

        self._setup_window()
        self._setup_canvas()
        self._bind_events()

        self._log(f"[INIT] Scenario: {self.scenario_id} ({self.scenario.get('name', '')})")
        self._log(f"[INIT] Steps: {len(self.scenario['steps'])}")
        self._log("[KEYS] Esc=quit  R=reset  N=next  ←/→=navigate  D=debug")
        self.render_step()

    # ----- window setup ----- #

    def _setup_window(self):
        self.root.title(f"PokerViewer — {self.scenario_id}")
        self.root.overrideredirect(True)  # убрать titlebar/borders
        self.root.configure(bg="black")
        if self.topmost:
            self.root.attributes("-topmost", True)
        # Позиция задастся в render_step после загрузки картинки

    def _setup_canvas(self):
        self.canvas = tk.Canvas(
            self.root,
            highlightthickness=0,
            borderwidth=0,
            bg="black",
            cursor="arrow",
        )
        self.canvas.pack()

    def _bind_events(self):
        self.canvas.bind("<Button-1>", self._on_click)
        # Клавиши ловим на root, чтобы фокус был у окна
        self.root.bind("<Key>", self._on_key)
        self.root.bind("<Escape>", lambda e: self._quit())
        self.root.bind("<r>", lambda e: self.reset())
        self.root.bind("<R>", lambda e: self.reset())
        self.root.bind("<n>", lambda e: self.next_step())
        self.root.bind("<N>", lambda e: self.next_step())
        self.root.bind("<Right>", lambda e: self.next_step())
        self.root.bind("<Left>", lambda e: self._prev_step())
        self.root.bind("<d>", lambda e: self._toggle_debug())
        self.root.bind("<D>", lambda e: self._toggle_debug())

    # ----- rendering ----- #

    def render_step(self):
        step = self._current_step()
        if step is None:
            return

        self.is_waiting = True
        self.selected_size = None
        self.slider_clicks = 0
        self.step_actions = []
        self.miss_clicks = 0

        try:
            img = load_image(step["image"])
        except Exception as e:
            self._log(f"[ERROR] Failed to load image '{step['image']}': {e}")
            return

        self.img_w, self.img_h = img.size

        # Размер/позиция окна — точно нативный размер картинки
        x, y = self.position
        self.root.geometry(f"{self.img_w}x{self.img_h}+{x}+{y}")
        self.canvas.config(width=self.img_w, height=self.img_h)

        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

        if self.debug:
            self._draw_debug_rects()

        self._log(
            f"[STEP {self.step_idx + 1}/{len(self.scenario['steps'])}] "
            f"{step.get('name', step['id'])} — {step.get('instruction', '')} "
            f"image={self.img_w}x{self.img_h}"
        )

    def _draw_debug_rects(self):
        step = self._current_step()
        for btn in step.get("buttons", []):
            cx = btn["x"] / 100.0 * self.img_w
            cy = btn["y"] / 100.0 * self.img_h
            left = cx - btn["width"] / 2
            top = cy - btn["height"] / 2
            right = left + btn["width"]
            bottom = top + btn["height"]
            self.canvas.create_rectangle(
                left, top, right, bottom,
                outline="red", width=2,
            )

    def _toggle_debug(self):
        self.debug = not self.debug
        self._log(f"[DEBUG] debug mode = {self.debug}")
        self.render_step()

    # ----- input handling ----- #

    def _on_click(self, event):
        if not self.is_waiting:
            return

        x, y = event.x, event.y
        if self.log_clicks:
            self._log(f"[CLICK] ({x}, {y})", also_file=True)

        step = self._current_step()
        for btn in step.get("buttons", []):
            cx = btn["x"] / 100.0 * self.img_w
            cy = btn["y"] / 100.0 * self.img_h
            left = cx - btn["width"] / 2
            top = cy - btn["height"] / 2
            right = left + btn["width"]
            bottom = top + btn["height"]
            if left <= x <= right and top <= y <= bottom:
                self._handle_action(btn)
                return
        self._handle_missclick()

    def _on_key(self, event):
        # Заглушка, чтобы не терялся фокус. Реальные шорткаты навешаны отдельно.
        pass

    # ----- action validation (логика из docs/js/emulator.js) ----- #

    def _handle_action(self, btn):
        step = self._current_step()

        if btn["type"] in SIZE_TYPES:
            self.selected_size = btn["type"]
            self.slider_clicks = 0
            self._log(f"[SIZE] selected={self.selected_size} ({btn['label']})")
            return

        if btn["type"] == "slider_click":
            self.slider_clicks += 1
            self._log(f"[SLIDER] click #{self.slider_clicks}")
            return

        if btn["type"] in ACTION_TYPES:
            expected = step["correctAction"]
            is_action_ok = btn["type"] == expected["type"]

            expected_size = expected.get("size")
            expected_slider = expected.get("sliderClicks", 0) or 0

            if expected_size:
                is_size_ok = self.selected_size == f"bet_{expected_size}"
            else:
                is_size_ok = self.selected_size is None

            is_slider_ok = self.slider_clicks == expected_slider
            is_size_ok_full = is_size_ok and is_slider_ok
            size_error = not is_size_ok_full
            is_correct = is_action_ok and is_size_ok_full

            self.is_waiting = False

            action_desc = self._action_description(btn, step)
            expected_desc = self._expected_description(expected, step)

            self.results.append({
                "step": step.get("name", step["id"]),
                "action": action_desc,
                "expected": expected_desc,
                "correct": is_correct,
                "action_type": btn["type"],
                "expected_type": expected["type"],
                "selected_size": self.selected_size,
                "expected_size": expected_size,
                "slider_clicks": self.slider_clicks,
                "expected_slider_clicks": expected_slider,
                "size_error": size_error,
            })

            if is_correct:
                self._log(f"[STEP {self.step_idx + 1}] ✓ {action_desc}")
            else:
                if size_error:
                    if expected_size and not self.selected_size:
                        reason = f"не выбран базовый сайз ({expected_size}%)"
                    elif not expected_size and self.selected_size:
                        reason = "выбран лишний сайз"
                    elif not is_size_ok:
                        actual = self.selected_size.replace("bet_", "") if self.selected_size else "—"
                        reason = f"базовый сайз {actual}% вместо {expected_size}%"
                    elif expected_slider and not self.slider_clicks:
                        reason = f"не нажат ползунок (нужно {expected_slider}×)"
                    elif not expected_slider and self.slider_clicks:
                        reason = f"лишние клики по ползунку ({self.slider_clicks}×)"
                    else:
                        reason = f"ползунок: {self.slider_clicks}× вместо {expected_slider}×"
                    self._log(f"[STEP {self.step_idx + 1}] ✗ {action_desc} — {reason} (ожидалось: {expected_desc})")
                else:
                    self._log(f"[STEP {self.step_idx + 1}] ✗ {action_desc} — действие: {btn['type']} вместо {expected['type']} (ожидалось: {expected_desc})")

            self._unlock_and_maybe_summary()

    def _handle_missclick(self):
        if not self.is_waiting:
            return
        self.miss_clicks += 1
        self.is_waiting = False

        step = self._current_step()
        expected = step["correctAction"]
        expected_size = expected.get("size")
        expected_slider = expected.get("sliderClicks", 0) or 0

        self.results.append({
            "step": step.get("name", step["id"]),
            "action": f"Клик мимо кнопки ({self.miss_clicks}×)",
            "expected": "Клик по одной из кнопок на изображении",
            "correct": False,
            "action_type": "missclick",
            "expected_type": expected["type"],
            "selected_size": self.selected_size,
            "expected_size": expected_size,
            "slider_clicks": self.slider_clicks,
            "expected_slider_clicks": expected_slider,
            "size_error": True,
            "missclick": True,
        })

        self._log(f"[STEP {self.step_idx + 1}] ✗ Клик мимо кнопки ({self.miss_clicks}×)")

        self._unlock_and_maybe_summary()

    def _unlock_and_maybe_summary(self):
        if self.step_idx >= len(self.scenario["steps"]) - 1:
            # Последний шаг — через секунду покажем итог и сменим картинку на первый шаг
            self.root.after(1500, self._show_summary_and_reset)
        else:
            self.root.after(800, self.next_step)

    # ----- descriptions ----- #

    def _action_description(self, btn, step):
        parts = []
        if self.selected_size:
            size_btn = next(
                (b for b in step["buttons"] if b["type"] == self.selected_size),
                None,
            )
            if size_btn:
                parts.append(size_btn["label"])
        if self.slider_clicks:
            parts.append(f"Slider ({self.slider_clicks}×)")
        parts.append(btn["label"])
        if btn.get("amount"):
            parts.append(btn["amount"])
        return " → ".join(parts) if parts else btn["label"]

    def _expected_description(self, expected, step):
        parts = []
        if expected.get("size"):
            parts.append(f"{expected['size']}%")
        slider = expected.get("sliderClicks", 0) or 0
        if slider:
            parts.append(f"Slider ({slider}×)")
        parts.append(expected["label"])
        if expected.get("amount"):
            parts.append(expected["amount"])
        return " → ".join(parts) if parts else expected["label"]

    # ----- step navigation ----- #

    def next_step(self):
        if self.step_idx < len(self.scenario["steps"]) - 1:
            self.step_idx += 1
            self.render_step()

    def _prev_step(self):
        if self.step_idx > 0:
            self.step_idx -= 1
            self.render_step()

    def reset(self):
        self.step_idx = 0
        self.results = []
        self._log("[RESET] scenario restarted")
        self.render_step()

    # ----- summary ----- #

    def _show_summary_and_reset(self):
        self._show_summary()
        self.reset()

    def _show_summary(self):
        total = len(self.results)
        correct = sum(1 for r in self.results if r["correct"])
        miss = sum(1 for r in self.results if r.get("missclick"))
        self._log("=" * 60)
        self._log(f"[SUMMARY] {correct}/{total} правильных ответов")
        if miss:
            self._log(f"[SUMMARY] {miss} промах(ов) мимо кнопок")
        for i, r in enumerate(self.results, 1):
            mark = "✓" if r["correct"] else "✗"
            line = f"  {i}. {mark} {r['step']}: {r['action']}"
            if not r["correct"]:
                line += f"  (ожидалось: {r['expected']})"
            self._log(line)
        self._log("=" * 60)

    # ----- helpers ----- #

    def _current_step(self):
        steps = self.scenario["steps"]
        if self.step_idx >= len(steps):
            return None
        return steps[self.step_idx]

    def _quit(self):
        self._log("[QUIT]")
        try:
            self.root.destroy()
        except Exception:
            pass

    def _log(self, message, also_file=False):
        ts = time.strftime("%H:%M:%S")
        line = f"{ts} {message}"
        print(line, flush=True)
        if also_file and self.log_clicks:
            if self.click_log_path is None:
                self.click_log_path = CACHE_DIR / f"clicks_{int(time.time())}.log"
            with self.click_log_path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")


# ---------------------------- CLI ---------------------------- #

def main():
    here = Path(__file__).parent
    repo_root = here.parent

    ap = argparse.ArgumentParser(
        description="Poker Emulator Viewer — borderless нативный просмотр скриншотов",
    )
    ap.add_argument("--scenario", help="ID сценария из scenarios.js (обязателен без --list)")
    ap.add_argument(
        "--scenarios-js",
        default=str(repo_root / "docs" / "js" / "scenarios.js"),
        help="Путь к scenarios.js (default: docs/js/scenarios.js)",
    )
    ap.add_argument(
        "--position",
        default="0,0",
        help="X,Y позиция окна на экране (default: 0,0)",
    )
    ap.add_argument(
        "--no-topmost",
        action="store_true",
        help="Не делать окно always-on-top (по умолчанию поверх всех)",
    )
    ap.add_argument(
        "--debug",
        action="store_true",
        help="Показывать красные рамки вокруг кнопок (для отладки позиций)",
    )
    ap.add_argument(
        "--log-clicks",
        action="store_true",
        help="Логировать координаты всех кликов в viewer/cache/clicks_<ts>.log",
    )
    ap.add_argument(
        "--list",
        action="store_true",
        help="Только вывести список сценариев и выйти",
    )
    args = ap.parse_args()

    scenarios = parse_scenarios_js(args.scenarios_js)

    if args.list:
        for sid, name in list_scenarios(scenarios):
            print(f"  {sid}\t{name}")
        return 0

    if not args.scenario:
        ap.error("--scenario is required (or use --list)")

    try:
        x, y = (int(v) for v in args.position.split(","))
    except ValueError:
        print(f"Invalid --position: {args.position} (expected X,Y)", file=sys.stderr)
        return 2

    root = tk.Tk()
    try:
        PokerViewer(
            root,
            scenarios,
            args.scenario,
            position=(x, y),
            topmost=not args.no_topmost,
            debug=args.debug,
            log_clicks=args.log_clicks,
        )
        root.mainloop()
    except Exception as e:
        print(f"Fatal: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
