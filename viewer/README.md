# Poker Emulator Viewer (Desktop)

Десктопное приложение для отображения покерных скриншотов с валидацией действий.
**Нормальное оконное приложение** (НЕ override-redirect popup):

- Windowed mode: с менабаром, статусбаром, скейлинг картинки под окно
- Fullscreen mode (F11): картинка в нативном размере, без chrome
- Закрытие через titlebar X (стандартный WM way)

Используется для тестирования покерного бота: бот делает скриншот окна
через HDMI capture и CV. В fullscreen режиме capture получает 1:1 копию
исходного скриншота.

## Зачем

Web-версия (`docs/index.html`) масштабирует картинку под размер окна браузера.
Бот с HDMI capture получает изображение неизвестного размера, что ломает CV
с конкретными настройками. Viewer показывает картинку **в её нативном
разрешении** (например, 1918×1078 для скриншотов 1080p) при включении fullscreen.

## Требования

- Python ≥ 3.9
- `tkinter` (часто идёт в комплекте; на Ubuntu/Debian:
  `sudo apt install python3-tk`)
- `Pillow`, `requests` (ставится из `requirements.txt`)

## Установка (через Makefile)

```bash
# Создаёт viewer/.venv, ставит зависимости, проверяет tkinter
make init
```

Под капотом: `python3 -m venv viewer/.venv` → `pip install -r viewer/requirements.txt`
→ проверка `import tkinter`. Системный Python **не трогается**.

## Запуск (через Makefile)

```bash
make list                          # список сценариев
make run SCENARIO=my_test          # запуск viewer
make run SCENARIO=my_test POSITION=1920,0  # на втором мониторе
make run SCENARIO=my_test DEBUG=1  # с красными рамками вокруг кнопок
make run SCENARIO=my_test NO_TOPMOST=1 LOG=1  # без always-on-top + лог кликов
make smoke                         # smoke-тесты без GUI
make check                         # проверить зависимости
make info                          # инфо о системе
make clean-cache                   # удалить кеш картинок
make clean                         # полная очистка (cache + venv)
make help                          # список всех команд
```

## Прямой запуск (без Makefile)

```bash
# Активировать venv вручную
source viewer/.venv/bin/activate
python3 viewer/viewer.py --scenario my_test
```

Или без активации:

```bash
viewer/.venv/bin/python viewer/viewer.py --scenario my_test
```

### CLI-флаги

```bash
--scenario ID         # ID сценария (обязателен, кроме --list)
--scenarios-js PATH   # путь к scenarios.js (default: docs/js/scenarios.js)
--position X,Y        # позиция окна (default: 0,0)
--no-topmost          # не делать always-on-top
--debug               # показать зоны кнопок
--log-clicks          # логировать координаты кликов
--list                # только список сценариев и выход
```

## Горячие клавиши

| Клавиша   | Действие                                          |
|-----------|---------------------------------------------------|
| `F11`     | Вкл/выкл fullscreen режим                         |
| `Esc`     | В fullscreen: выйти. В windowed: закрыть          |
| `Ctrl+Q` / `Ctrl+W` / `Ctrl+C` | Закрыть окно                  |
| `R`       | Сбросить тест (вернуться на шаг 1)                |
| `N` / `→` | Следующий шаг                                     |
| `←`       | Предыдущий шаг                                    |
| `D`       | Вкл/выкл отображение зон кнопок (debug)           |

## Меню

- **File**: Reset scenario, Quit
- **View**: Fullscreen, Show click areas, Log clicks to file
- **Scenario**: переключение между сценариями (радио)
- **Help**: About

## Закрытие окна

Нормальное desktop-приложение. Закрывается **пятью способами** (от самого надёжного к наименее):

| # | Способ | Описание |
|---|--------|----------|
| 1 | **Titlebar X** | Стандартный крестик ОС — посылает `WM_DELETE_WINDOW`, обрабатывается корректно |
| 2 | `Ctrl+Q` / `Ctrl+W` / `Ctrl+C` | Клавиатурные шорткаты |
| 3 | `Esc` | В windowed: закрыть. В fullscreen: выйти из fullscreen |
| 4 | **File → Quit** | Меню |
| 5 | `kill <PID>` (SIGTERM) | Из другого терминала, если всё зависло |

Клик мышью в области кнопки регистрируется как действие бота.
Результат пишется в консоль (stdout).

## Формат сценариев

Viewer читает `docs/js/scenarios.js` напрямую (без дублирования).
Координаты кнопок заданы в **процентах от размера картинки** —
при нативном отображении они автоматически становятся правильными
пиксельными координатами для бота.

Структура шага:

```javascript
{
    id: 'preflop',
    name: 'Префлоп',
    image: 'https://...',
    correctAction: {
        type: 'raise',          // fold/check/call/bet/raise
        label: 'Raise to',
        amount: '',
        size: '100',            // ожидаемый базовый сайз: 33/50/75/100
        sliderClicks: 3         // ожидаемое число кликов по ползунку
    },
    buttons: [
        { id: 'bet_100', type: 'bet_100', label: '100%',
          x: 71.1, y: 76.6, width: 40, height: 30 },
        { id: 'slider_click', type: 'slider_click',
          x: 82.6, y: 76.6, width: 40, height: 20 },
        { id: 'raise', type: 'raise', label: 'Raise to',
          x: 80.9, y: 84.0, width: 100, height: 60 }
    ]
}
```

## Логика валидации

Зеркалит логику из `docs/js/emulator.js`:

1. Клик по `bet_33/bet_50/bet_75/bet_100` → выбирает базовый сайз
2. Клик по `slider_click` → увеличивает счётчик (сбрасывает счётчик при выборе нового сайза)
3. Клик по `fold/check/call/bet/raise` → проверяет:
   - Совпадает ли тип действия с `correctAction.type`
   - Совпадает ли выбранный базовый сайз с `correctAction.size`
   - Совпадает ли число кликов ползунка с `correctAction.sliderClicks`
4. Клик мимо всех кнопок → `missclick` (тест провален)

Пример вывода в консоль:

```
12:34:56 [STEP 1/1] Префлоп — Ваше действие на Префлоп? image=1918x1078
12:35:10 [SIZE] selected=bet_100 (100%)
12:35:11 [SLIDER] click #1
12:35:11 [SLIDER] click #2
12:35:12 [SLIDER] click #3
12:35:12 [STEP 1] ✓ 100% → Slider (3×) → Raise to
============================================================
12:35:12 [SUMMARY] 1/1 правильных ответов
  1. ✓ Префлоп: 100% → Slider (3×) → Raise to
============================================================
```

## Проверка (имитация HDMI capture)

```bash
# Узнать geometry активного окна
xdotool getactivewindow getwindowgeometry
# → position: 0,0, size: 1918x1078, без декораций

# Снять скриншот той же области
scrot -a 0,0,1918,1078 capture.png

# Сравнить с исходником
python3 -c "
from PIL import Image, ImageChops
a = Image.open('viewer/cache/<hash>.bin')
b = Image.open('capture.png')
print('identical:', ImageChops.difference(a, b).getbbox() is None)
"
```

## Интеграция с Arduino (на будущее)

Когда подключите Arduino UNO + Arduino Micro PRO как HID-мышь:

- Arduino будет посылать абсолютные координаты клика
- Viewer получает события через tkinter стандартным способом
- Логирование в stdout можно перенаправить: `python3 viewer.py --scenario X > viewer.log`
- С флагом `--log-clicks` все клики (с координатами) пишутся в `viewer/cache/clicks_<ts>.log` для последующего анализа

## Тестирование

```bash
# Прогон smoke-тестов без GUI (без tkinter)
python3 viewer/test_smoke.py
```

Проверяет: парсинг scenarios.js, скачивание и кеш, нативный размер картинки,
расчёт пиксельных координат, валидацию действий, missclick.

## Файлы

```
viewer/
├── viewer.py            ← главный класс PokerViewer + CLI
├── scenario_loader.py   ← парсер docs/js/scenarios.js
├── image_loader.py      ← загрузка/кеш картинок
├── test_smoke.py        ← smoke-тесты без GUI
├── requirements.txt     ← Pillow, requests
├── README.md            ← этот файл
└── cache/               ← кеш скачанных картинок (в .gitignore)
```
