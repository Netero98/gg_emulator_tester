# Poker Emulator ☁️

Эмулятор покерного стола для тестирования ботов с использованием реальных скриншотов по URL.

**Полностью облачный**: Изображения хранятся на GitHub Pages / CDN, код - в репозитории.

## Быстрый старт

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/yourname/poker-emulator.git

# 2. Откройте index.html в браузере
open docs/index.html
```

Или откройте прямо на GitHub Pages:
```
https://yourname.github.io/gg_emulator_tester/
```

## 🖥️ Desktop Viewer (для HDMI capture)

Если бот читает экран через **HDMI capture** и использует CV с конкретными
настройками — web-версия не подходит (картинка масштабируется под окно).
Используйте десктопный viewer из `viewer/`:

```bash
# Установка (создаёт venv в viewer/.venv, ничего не ставит в систему)
make init

# Проверить зависимости
make check

# Посмотреть доступные сценарии
make list

# Запустить viewer
make run SCENARIO=my_test
```

Откроется **borderless окно точно по нативному размеру картинки** (например,
1918×1078) в позиции (0, 0) — без titlebar/адресной строки/UI браузера.
HDMI capture получает 1:1 копию исходного скриншота.

Подробнее: [`viewer/README.md`](viewer/README.md).

## Архитектура

```
GitHub Pages / CDN          GitHub Repository
┌─────────────────┐         ┌──────────────────────────┐
│  preflop.png    │         │   docs/                  │
│  flop.png       │◄────────┤   ├── index.html         │ ← web-тесты
│  turn.png       │  URL    │   ├── configurator.html  │
│  river.png      │         │   └── js/scenarios.js    │ ← source of truth
└─────────────────┘         │                          │
                            │   viewer/                │ ← desktop для HDMI
                            │   ├── viewer.py          │
                            │   ├── scenario_loader.py │
                            │   └── image_loader.py    │
                            └──────────────────────────┘
```

**Изображения** загружаются по URL (не хранятся локально)  
**Код** хранится в репозитории  
**Сценарии** добавляются через pull requests

## Создание нового теста

### Шаг 1: Подготовьте изображения

1. Сделайте скриншоты для каждой улицы (префлоп, флоп, турн, ривер)
2. Загрузите их в интернет (варианты):
   - **GitHub Pages** (рекомендуется)
   - **imgur**
   - **Любой хостинг изображений**

### Шаг 2: Используйте configurator.html

Откройте `docs/configurator.html` локально или на GitHub Pages.

**Заполните форму:**
```
Название теста (ID):       qq_4bet_pot
Название отображения:      QQ - 4бет пот
Описание:                  Тест на 4бет пот с дамами

Базовый URL (опционально): https://yourname.github.io/poker-images/
                           (или оставьте пустым для прямых URL)
```

**Для каждой улицы:**
1. Выберите улицу (Префлоп → Флоп → Турн → Ривер)
2. Укажите изображение одним из способов:
   - **Вставить URL** в поле ввода (https://..., http://...)
   - **Нажать "📁 Из photos/"** — выбрать из локальной папки `docs/photos/`
3. Дождитесь загрузки изображения
4. Настройте кнопки:
   - Добавьте кнопки (Fold/Check/Call/Bet/Raise)
   - Перетащите на нужное место на скриншоте
5. Выберите правильное действие
6. Добавьте объяснения

**Локальные фотки (`docs/photos/`):**
1. Положите скриншоты в `docs/photos/` (можно с подпапками, например `docs/photos/AKs/1.png`)
2. Запустите `make photos-manifest` — это просканирует папку и создаст `docs/photos.js`
3. Откройте `docs/configurator.html` (можно по `file://`, без сервера)
4. Нажмите **"📁 Из photos/"** — появятся превью всех картинок
5. Клик на превью → URL `photos/AKs/1.png` (относительный) встанет в инпут
6. В `scenarios.js` сохраняется относительный URL, **работает одинаково**:
   - в Python viewer (`make run`)
   - в web `docs/index.html` (если хостить из `docs/`, например через GitHub Pages)

**Почему `photos.js` а не `photos.json`?** Chrome блокирует `fetch()` между `file://` URL'ами по CORS.
`<script src="photos.js">` таких ограничений не имеет и работает на `file://` в любом браузере.

Никакого сервера не нужно — конфигуратор загружает `photos.js` через `<script>`, фотки подгружает по относительным путям.

### Шаг 3: Получите код

Нажмите "📋 Копировать код". Будет сгенерирован:

```javascript
'qq_4bet_pot': {
    name: 'QQ - 4бет пот',
    description: 'Тест на 4бет пот с дамами',
    steps: [
        {
            id: 'preflop',
            name: 'Префлоп',
            image: 'https://yourname.github.io/poker-images/qq_4bet_pot_preflop.png',
            instruction: 'Ваше действие на Префлоп?',
            correctAction: {
                type: 'raise',
                label: 'Raise',
                amount: '$0.24'
            },
            buttons: [
                {
                    id: 'fold',
                    type: 'fold',
                    label: 'Fold',
                    x: 74.5,
                    y: 88.5,
                    width: 140,
                    height: 65
                },
                // ... другие кнопки
            ],
            feedback: {
                correct: 'Отлично! С QQ нужно делать 4бет для велью.',
                incorrect: 'Неправильно. С QQ нужно ререйзить для велью.'
            }
        },
        // ... flop, turn, river
    ]
}
```

### Шаг 3: Добавьте в репозиторий

1. **Откройте `docs/js/scenarios.js`**
2. **Добавьте код** в объект `SCENARIOS`:
```javascript
const SCENARIOS = {
    'aks_3bet_cbet': { ... },  // существующий
    
    // ВСТАВЬТЕ НОВЫЙ СЦЕНАРИЙ ЗДЕСЬ:
    'qq_4bet_pot': {
        name: 'QQ - 4бет пот',
        ...
    }
};
```

3. **Закоммитьте и запушьте**:
```bash
git add .
git commit -m "Add QQ 4bet pot test scenario"
git push origin main
```

### Шаг 4: Готово! 🎉

Тест автоматически доступен на GitHub Pages!

## Почему это круто

✅ **Никаких локальных файлов** - всё в облаке  
✅ **Мгновенный деплой** - push → готово  
✅ **Версионирование** - история изменений в git  
✅ **Коллаборация** - pull requests для новых тестов  
✅ **CDN** - изображения загружаются быстро с GitHub Pages  

## API для ботов

### Python + Selenium

```python
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()

# Локально
driver.get('file:///path/to/docs/index.html')

# Или на GitHub Pages
driver.get('https://yourname.github.io/gg_emulator_tester/')

# Выбрать тест
driver.find_element(By.ID, 'scenario-select').send_keys('QQ - 4бет пот')

# Кликнуть кнопку
fold_btn = driver.find_element(By.CSS_SELECTOR, '[data-action="fold"]')
fold_btn.click()

# Проверить результат
result = driver.find_element(By.ID, 'result-display')
print(result.text)  # "✓ Правильно!" или "✗ Неправильно..."
```

### Python + PyAutoGUI

```python
import pyautogui

# Координаты из scenarios.js (в процентах)
# x: 74.5%, y: 88.5%

screen = pyautogui.size()
x = int(screen.width * 0.745)
y = int(screen.height * 0.885)

pyautogui.click(x, y)
```

## Структура репозитория

```
gg_emulator_tester/
├── docs/                           ← GitHub Pages (корень сайта) и основной код
│   ├── index.html                  ← основное web-приложение
│   ├── configurator.html           ← создание тестов
│   ├── photos/                     ← локальные скриншоты (для сценариев)
│   ├── photos.js                   ← manifest фоток (генерируется `make photos-manifest`)
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── scenarios.js            ← все тесты здесь (source of truth)
│       └── emulator.js
│
├── viewer/                         ← ДЕСКТОПНЫЙ viewer (для HDMI capture)
│   ├── viewer.py                   ← главный класс + CLI
│   ├── scenario_loader.py          ← парсер scenarios.js
│   ├── image_loader.py             ← загрузка/кеш картинок
│   ├── test_smoke.py               ← smoke-тесты без GUI
│   ├── requirements.txt
│   └── README.md
│
└── README.md                       ← этот файл
```

**Изображения НЕ хранятся в репозитории** - только URL!

## Требования

- Любой браузер
- Никаких зависимостей
- Никакого сервера
- Работает оффлайн (если изображения закэшированы)

## Лицензия

MIT License
