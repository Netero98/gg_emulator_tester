"""
Poker Emulator Viewer — десктопное приложение для отображения покерных скриншотов.

Нормальное оконное приложение (НЕ override-redirect popup) с:
- Менюбаром (File, View, Scenario, Help)
- Status bar
- Windowed mode (по умолчанию): изображение с оставлением aspect ratio
- Fullscreen mode (F11): изображение в нативном размере для HDMI capture
- Стандартное закрытие через titlebar X, Ctrl+Q, File → Quit, Esc (выход из FS)

Запуск:
    python viewer.py --scenario my_test
    python viewer.py --scenario my_test --position 1920,0  # на втором мониторе
    python viewer.py --scenario my_test --no-topmost --start-fullscreen
"""
import argparse
import sys
import time
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk

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
                 topmost=True, debug=False, log_clicks=False,
                 start_fullscreen=False):
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
        self.is_fullscreen = False

        # runtime state
        self.step_idx = 0
        self.results = []
        self.selected_size = None
        self.slider_clicks = 0
        self.step_actions = []
        self.miss_clicks = 0
        self.is_waiting = True

        # image / canvas state
        self.img_w = 0
        self.img_h = 0
        self.original_pil_image = None
        self.tk_img = None
        self.img_scale = 1.0
        self.img_offset_x = 0
        self.img_offset_y = 0

        self._saved_menubar = None
        self._click_log_path = None

        self._setup_window()
        self._setup_menubar()
        self._setup_canvas()
        self._setup_statusbar()
        self._bind_events()

        if self.topmost:
            self.root.attributes("-topmost", True)

        self._log(f"[INIT] Scenario: {self.scenario_id} ({self.scenario.get('name', '')})")
        self._log(f"[INIT] Steps: {len(self.scenario['steps'])}")
        self._log("[KEYS] F11=fullscreen  Esc=exit-FS/quit  Ctrl+Q=quit  R=reset  "
                  "N/→=next  ←=prev  D=debug  Right-click=menu")
        self.render_step()

        if start_fullscreen:
            self.root.after(100, self._toggle_fullscreen)

    # ----- window ----- #

    def _setup_window(self):
        # Нормальное окно (НЕ override-redirect) — так WM управляет им
        # стандартным способом: titlebar X, Alt+F4, fullscreen, etc.
        self.root.title(f"Poker Viewer — {self.scenario_id}")
        self.root.minsize(640, 480)
        self.root.configure(bg="#000")
        # Закрытие через titlebar X и Alt+F4
        self.root.protocol("WM_DELETE_WINDOW", self._quit)
        # SIGINT (Ctrl+C) — перехватываем и закрываем аккуратно
        import signal
        signal.signal(signal.SIGINT, lambda *_: self.root.after(0, self._quit))

    def _setup_menubar(self):
        menubar = tk.Menu(self.root)

        # File
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Reset scenario", accelerator="R", command=self.reset)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", accelerator="Ctrl+Q", command=self._quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # View
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(
            label="Fullscreen",
            accelerator="F11",
            command=self._toggle_fullscreen,
        )
        self._fullscreen_index = view_menu.index("end")
        view_menu.add_checkbutton(
            label="Show click areas (debug)",
            accelerator="D",
            command=self._toggle_debug,
        )
        view_menu.add_checkbutton(
            label="Log clicks to file",
            command=self._toggle_log_clicks,
        )
        menubar.add_cascade(label="View", menu=view_menu)

        # Scenario (radio)
        self.scenario_menu = tk.Menu(menubar, tearoff=0)
        for sid, sname in list_scenarios(self.scenarios):
            self.scenario_menu.add_radiobutton(
                label=f"{sid}  —  {sname}",
                value=sid,
                command=lambda s=sid: self._load_scenario(s),
            )
        menubar.add_cascade(label="Scenario", menu=self.scenario_menu)

        # Help
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)
        self.menubar = menubar

    def _setup_canvas(self):
        self.canvas = tk.Canvas(
            self.root,
            highlightthickness=0,
            borderwidth=0,
            bg="#000",
            cursor="arrow",
        )
        self.canvas.pack(side="top", fill="both", expand=True)

    def _setup_statusbar(self):
        self.status_var = tk.StringVar(value="Ready")
        self.statusbar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bd=1, relief="sunken", anchor="w",
            bg="#222", fg="#fff",
            font=("Arial", 10),
            padx=8, pady=2,
        )
        self.statusbar.pack(side="bottom", fill="x")

    def _bind_events(self):
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # Клавиатурные шорткаты
        self.root.bind("<F11>", lambda e: self._toggle_fullscreen())
        self.root.bind("<Escape>", self._on_escape)
        self.root.bind("<Control-q>", lambda e: self._quit())
        self.root.bind("<Control-w>", lambda e: self._quit())
        self.root.bind("<Control-c>", lambda e: self._quit())
        self.root.bind("<r>", lambda e: self.reset())
        self.root.bind("<R>", lambda e: self.reset())
        self.root.bind("<n>", lambda e: self.next_step())
        self.root.bind("<N>", lambda e: self.next_step())
        self.root.bind("<Right>", lambda e: self.next_step())
        self.root.bind("<Left>", lambda e: self._prev_step())
        self.root.bind("<d>", lambda e: self._toggle_debug())
        self.root.bind("<D>", lambda e: self._toggle_debug())

    def _on_escape(self, event=None):
        if self.is_fullscreen:
            self._toggle_fullscreen()
        else:
            self._quit()

    def _on_canvas_resize(self, event):
        if self.original_pil_image is not None:
            self._render_image()

    # ----- fullscreen ----- #

    def _toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)
        if self.is_fullscreen:
            # Скрыть menubar и statusbar
            self._saved_menubar = self.root.cget("menu")
            self.root.config(menu="")
            self.statusbar.pack_forget()
        else:
            # Вернуть menubar и statusbar
            if self._saved_menubar is not None:
                self.root.config(menu=self._saved_menubar)
            self.statusbar.pack(side="bottom", fill="x")
        self._log(f"[FULLSCREEN] {'on' if self.is_fullscreen else 'off'}")
        # Перерисовать картинку под новый размер canvas
        self.root.after(50, self._render_image)

    # ----- scenario loading / rendering ----- #

    def _load_scenario(self, scenario_id):
        if scenario_id == self.scenario_id:
            return
        self.scenario_id = scenario_id
        self.scenario = self.scenarios[scenario_id]
        self.step_idx = 0
        self.results = []
        self.root.title(f"Poker Viewer — {scenario_id}")
        self._log(f"[SCENARIO] switched to {scenario_id}")
        self.render_step()

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
            self.original_pil_image = img
            self.img_w, self.img_h = img.size
        except Exception as e:
            self._log(f"[ERROR] Failed to load image '{step['image']}': {e}")
            self.status_var.set(f"Error loading image: {e}")
            return

        # Подогнать размер окна под нативный размер картинки + chrome
        # (если ещё не в fullscreen)
        if not self.is_fullscreen:
            x, y = self.position
            # tkinter обычно добавляет ~30px titlebar, ~5px borders сверху-снизу
            chrome_h = 90
            chrome_w = 20
            self.root.geometry(f"{self.img_w + chrome_w}x{self.img_h + chrome_h}+{x}+{y}")
            self.root.update_idletasks()

        self._render_image()
        self._update_status()

        self._log(
            f"[STEP {self.step_idx + 1}/{len(self.scenario['steps'])}] "
            f"{step.get('name', step['id'])} — image={self.img_w}x{self.img_h}"
        )

    def _render_image(self):
        """Отрисовать картинку на canvas.

        Windowed: scaled до canvas с сохранением aspect ratio
        Fullscreen: native size, центрирована (с чёрными полосами если screen != image)
        """
        if self.original_pil_image is None:
            return

        self.canvas.update_idletasks()
        canvas_w = max(self.canvas.winfo_width(), 1)
        canvas_h = max(self.canvas.winfo_height(), 1)

        if self.is_fullscreen:
            # Native size, центрирована
            scale = 1.0
            img_to_show = self.original_pil_image
        else:
            # Scale to fit, не увеличивать если картинка меньше canvas
            scale_w = canvas_w / self.img_w
            scale_h = canvas_h / self.img_h
            scale = min(scale_w, scale_h, 1.0)
            new_w = max(1, int(self.img_w * scale))
            new_h = max(1, int(self.img_h * scale))
            if scale < 1.0:
                img_to_show = self.original_pil_image.resize((new_w, new_h), Image.LANCZOS)
            else:
                img_to_show = self.original_pil_image

        self.img_scale = scale
        self.tk_img = ImageTk.PhotoImage(img_to_show)
        self.canvas.delete("all")
        self.img_offset_x = (canvas_w - img_to_show.width) // 2
        self.img_offset_y = (canvas_h - img_to_show.height) // 2
        self.canvas.create_image(
            self.img_offset_x, self.img_offset_y,
            anchor="nw", image=self.tk_img,
        )

        if self.debug:
            self._draw_debug_rects()

    def _draw_debug_rects(self):
        step = self._current_step()
        if not step:
            return
        for btn in step.get("buttons", []):
            cx = self.img_offset_x + (btn["x"] / 100.0) * self.img_w * self.img_scale
            cy = self.img_offset_y + (btn["y"] / 100.0) * self.img_h * self.img_scale
            w = btn["width"] * self.img_scale
            h = btn["height"] * self.img_scale
            self.canvas.create_rectangle(
                cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2,
                outline="red", width=2,
            )

    def _update_status(self):
        step = self._current_step()
        if not step:
            return
        mode = "FULLSCREEN" if self.is_fullscreen else "windowed"
        self.status_var.set(
            f"Step {self.step_idx + 1}/{len(self.scenario['steps'])}: "
            f"{step.get('name', step['id'])}  |  {mode}  |  "
            f"image {self.img_w}×{self.img_h}  |  "
            f"F11=fullscreen  Ctrl+Q=quit  R=reset"
        )

    # ----- click handling ----- #

    def _on_click(self, event):
        x, y = event.x, event.y

        if not self.is_waiting:
            return

        # Конвертировать canvas coords → image coords
        img_x = (x - self.img_offset_x) / self.img_scale
        img_y = (y - self.img_offset_y) / self.img_scale

        if self.log_clicks:
            self._log(f"[CLICK] canvas=({x},{y}) image=({img_x:.0f},{img_y:.0f}) scale={self.img_scale:.3f}",
                      also_file=True)

        # Проверка: клик в пределах изображения?
        if (img_x < 0 or img_x >= self.img_w or
                img_y < 0 or img_y >= self.img_h):
            self._handle_missclick()
            return

        step = self._current_step()
        for btn in step.get("buttons", []):
            cx = btn["x"] / 100.0 * self.img_w
            cy = btn["y"] / 100.0 * self.img_h
            left = cx - btn["width"] / 2
            top = cy - btn["height"] / 2
            right = left + btn["width"]
            bottom = top + btn["height"]
            if left <= img_x <= right and top <= img_y <= bottom:
                self._handle_action(btn)
                return
        self._handle_missclick()

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

    def _toggle_debug(self):
        self.debug = not self.debug
        self._log(f"[DEBUG] debug mode = {self.debug}")
        self._render_image()

    def _toggle_log_clicks(self):
        self.log_clicks = not self.log_clicks
        self._log(f"[LOG] log clicks = {self.log_clicks}")

    def _show_about(self):
        about = (
            "Poker Emulator Viewer\n\n"
            f"Scenario: {self.scenario_id}\n"
            f"Steps: {len(self.scenario['steps'])}\n\n"
            "Горячие клавиши:\n"
            "  F11 — полноэкранный режим\n"
            "  Esc — выход из fullscreen / закрыть\n"
            "  Ctrl+Q — закрыть\n"
            "  R — сбросить сценарий\n"
            "  N / → — следующий шаг\n"
            "  ← — предыдущий шаг\n"
            "  D — показать зоны кнопок"
        )
        # Простое info-окно
        try:
            from tkinter import messagebox
            messagebox.showinfo("Poker Emulator Viewer", about)
        except Exception:
            self._log(about)

    def _quit(self):
        if getattr(self, "_quitting", False):
            return
        self._quitting = True
        self._log("[QUIT]")
        # Пытаемся выйти штатно
        try:
            self.root.quit()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass
        # Если через ~0.5с процесс всё ещё жив — принудительный выход
        import threading
        def _force_exit():
            import os
            os._exit(0)
        threading.Timer(0.5, _force_exit).start()

    def _log(self, message, also_file=False):
        ts = time.strftime("%H:%M:%S")
        line = f"{ts} {message}"
        print(line, flush=True)
        if also_file and self.log_clicks:
            if self._click_log_path is None:
                self._click_log_path = CACHE_DIR / f"clicks_{int(time.time())}.log"
            with self._click_log_path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")


# ---------------------------- CLI ---------------------------- #

def main():
    here = Path(__file__).parent
    repo_root = here.parent

    ap = argparse.ArgumentParser(
        description="Poker Emulator Viewer — нормальное desktop-приложение для покерных скриншотов",
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
        help="Не делать always-on-top",
    )
    ap.add_argument(
        "--debug",
        action="store_true",
        help="Показывать красные рамки вокруг кнопок",
    )
    ap.add_argument(
        "--log-clicks",
        action="store_true",
        help="Логировать координаты всех кликов",
    )
    ap.add_argument(
        "--start-fullscreen",
        action="store_true",
        help="Сразу запустить в fullscreen (для HDMI capture)",
    )
    ap.add_argument(
        "--list",
        action="store_true",
        help="Только вывести список сценариев и выйти",
    )
    ap.add_argument(
        "--self-test",
        action="store_true",
        help="Запустить viewer, программно кликнуть в bet_100, проверить реакцию, выйти",
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
        viewer = PokerViewer(
            root,
            scenarios,
            args.scenario,
            position=(x, y),
            topmost=not args.no_topmost,
            debug=args.debug,
            log_clicks=args.log_clicks,
            start_fullscreen=args.start_fullscreen,
        )

        if args.self_test:
            root.update_idletasks()
            # Кликаем в центр bet_100
            btn = next(
                (b for b in viewer.scenario["steps"][0]["buttons"]
                 if b["id"] == "bet_100"),
                None,
            )
            if btn:
                cx = viewer.img_offset_x + (btn["x"] / 100.0) * viewer.img_w * viewer.img_scale
                cy = viewer.img_offset_y + (btn["y"] / 100.0) * viewer.img_h * viewer.img_scale
                print(f"[SELFTEST] simulating click at canvas ({cx:.0f}, {cy:.0f})")
                root.after(500, lambda: _self_test_click(viewer, root, int(cx), int(cy)))
            root.mainloop()
            return 0

        root.mainloop()
    except Exception as e:
        print(f"Fatal: {e}", file=sys.stderr)
        return 1
    return 0


def _self_test_click(viewer, root, x, y):
    """Программно симулирует клик в координаты (x, y) и выходит."""
    print(f"[SELFTEST] generating <Button-1> at ({x}, {y})")
    viewer.canvas.event_generate("<Button-1>", x=x, y=y)
    root.update_idletasks()
    root.update()
    print(f"[SELFTEST] after click: is_waiting={viewer.is_waiting}, selected_size={viewer.selected_size}")
    root.after(100, viewer._quit)


if __name__ == "__main__":
    sys.exit(main())
