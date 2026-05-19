# Poker Emulator ☁️

Эмулятор покерного стола для тестирования ботов с использованием реальных скриншотов по URL.

**Полностью облачный**: Изображения хранятся на GitHub Pages / CDN, код - в репозитории.

## Быстрый старт

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/yourname/poker-emulator.git

# 2. Откройте index.html в браузере
open poker-emulator/index.html
```

Или откройте прямо на GitHub Pages:
```
https://yourname.github.io/poker-emulator/
```

## Архитектура

```
GitHub Pages / CDN          GitHub Repository
┌─────────────────┐         ┌─────────────────┐
│  preflop.png    │         │   index.html    │
│  flop.png       │◄────────┤   scenarios.js  │
│  turn.png       │  URL    │   emulator.js   │
│  river.png      │         └─────────────────┘
└─────────────────┘
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

Откройте `configurator.html` локально или на GitHub Pages.

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
2. Введите URL изображения:
   - С базовым URL: `qq_4bet_pot_preflop.png` (авто-дополнение)
   - Или полный URL: `https://i.imgur.com/abc123.png`
3. Дождитесь загрузки изображения
4. Настройте кнопки:
   - Добавьте кнопки (Fold/Check/Call/Bet/Raise)
   - Перетащите на нужное место на скриншоте
5. Выберите правильное действие
6. Добавьте объяснения

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

### Шаг 4: Добавьте в репозиторий

1. **Откройте `js/scenarios.js`**
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

3. **Добавьте опцию в `index.html`**:
```html
<select id="scenario-select">
    <option value="aks_3bet_cbet">AKs - 3бет -> цбет -> чек -> фолд</option>
    <option value="qq_4bet_pot">QQ - 4бет пот</option>  <!-- НОВОЕ -->
</select>
```

4. **Закоммитьте и запушьте**:
```bash
git add .
git commit -m "Add QQ 4bet pot test scenario"
git push origin main
```

### Шаг 5: Готово! 🎉

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
driver.get('file:///path/to/poker-emulator/index.html')

# Или на GitHub Pages
driver.get('https://yourname.github.io/poker-emulator/')

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
poker-emulator/
├── index.html              ← основное приложение
├── configurator.html       ← создание тестов
├── README.md
├── css/
│   └── style.css
└── js/
    ├── scenarios.js        ← все тесты здесь
    └── emulator.js
```

**Изображения НЕ хранятся в репозитории** - только URL!

## Требования

- Любой браузер
- Никаких зависимостей
- Никакого сервера
- Работает оффлайн (если изображения закэшированы)

## Лицензия

MIT License
