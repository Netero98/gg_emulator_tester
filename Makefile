# Poker Emulator Viewer — Makefile
#
# Использование:
#   make init                       — создать venv и поставить зависимости
#   make list                       — список доступных сценариев
#   make run SCENARIO=my_test       — запустить viewer
#   make run SCENARIO=my_test FULLSCREEN=1  — сразу в fullscreen (для HDMI capture)
#   make smoke                      — smoke-тесты без GUI
#   make check                      — проверить зависимости
#   make info                       — информация о системе
#   make clean-cache                — очистить кеш картинок
#   make clean                      — полная очистка (cache + venv)
#   make help                       — список всех команд

VENV := viewer/.venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip

# Defaults (перекрываются через make run SCENARIO=... POSITION=... NO_TOPMOST=1 DEBUG=1 LOG=1 FULLSCREEN=1)
POSITION ?= 0,0

.DEFAULT_GOAL := help

.PHONY: help all init check run smoke test list info clean clean-cache verify-close run-debug photos-manifest

help: ## Показать список команд
	@echo "Poker Emulator Viewer — Makefile"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

all: init ## Алиас для init

init: ## Создать venv и установить зависимости
	@if [ ! -d "$(VENV)" ]; then \
		echo "→ Создаю venv в $(VENV)..."; \
		python3 -m venv $(VENV) 2>&1 || { \
			echo ""; \
			echo "✗ Не удалось создать venv."; \
			echo "  Установите в систему: sudo apt install python3-venv"; \
			exit 1; \
		}; \
	else \
		echo "→ venv уже существует: $(VENV)"; \
	fi
	@echo "→ Обновляю pip..."
	@$(PIP) install --upgrade pip --quiet
	@echo "→ Устанавливаю зависимости из viewer/requirements.txt..."
	@$(PIP) install -r viewer/requirements.txt
	@echo "→ Проверяю tkinter..."
	@if $(PY) -c "import tkinter" 2>/dev/null; then \
		echo "  ✓ tkinter OK"; \
	else \
		echo "  ✗ tkinter НЕ НАЙДЕН"; \
		echo "    Установите в систему: sudo apt install python3-tk"; \
		exit 1; \
	fi
	@echo ""
	@echo "✓ Установка завершена."
	@echo "  Посмотрите сценарии: make list"
	@echo "  Запустите viewer:    make run SCENARIO=my_test"

check: ## Проверить зависимости (без изменений)
	@printf "Python:   %s\n" "$$(python3 --version 2>&1)"
	@printf "Venv:     %s\n" "$$(test -x $(PY) && echo OK || echo MISSING)"
	@if $(PY) -c "import tkinter" 2>/dev/null; then \
		echo "tkinter:  OK"; \
	else \
		echo "tkinter:  ✗ sudo apt install python3-tk"; \
	fi
	@$(PY) -c "import PIL; print('Pillow:   ', PIL.__version__)" 2>/dev/null || echo "Pillow:    ✗ make init"
	@$(PY) -c "import requests; print('requests:', requests.__version__)" 2>/dev/null || echo "requests:  ✗ make init"

run: ## Запустить viewer (SCENARIO=id [POSITION=0,0] [NO_TOPMOST=1] [DEBUG=1] [LOG=1] [FULLSCREEN=1])
	@test -x $(PY) || { echo "✗ venv не создан. Запустите: make init"; exit 1; }
	@test -n "$(SCENARIO)" || { echo "✗ Укажите SCENARIO=..."; $(MAKE) --no-print-directory list; exit 1; }
	@$(PY) viewer/viewer.py \
		--scenario $(SCENARIO) \
		--position $(POSITION) \
		$(if $(NO_TOPMOST),--no-topmost) \
		$(if $(DEBUG),--debug) \
		$(if $(LOG),--log-clicks) \
		$(if $(FULLSCREEN),--start-fullscreen)

smoke test: ## Прогнать smoke-тесты без GUI
	@test -x $(PY) || { echo "✗ venv не создан. Запустите: make init"; exit 1; }
	@$(PY) viewer/test_smoke.py

verify-close: ## Программно кликнуть в bet_100 (self-test) [SCENARIO=my_test]
	@test -x $(PY) || { echo "✗ venv не создан. Запустите: make init"; exit 1; }
	@$(PY) viewer/viewer.py --scenario $(or $(SCENARIO),my_test) --self-test

run-debug: ## Запустить viewer с логированием всех кликов в файл (для отладки)
	@test -x $(PY) || { echo "✗ venv не создан. Запустите: make init"; exit 1; }
	@test -n "$(SCENARIO)" || { echo "✗ Укажите SCENARIO=..."; $(MAKE) --no-print-directory list; exit 1; }
	@$(PY) viewer/viewer.py \
		--scenario $(SCENARIO) \
		--position $(POSITION) \
		--debug \
		--log-clicks

photos-manifest: ## Сгенерировать docs/photos.js (JS manifest фоток из docs/photos/)
	@$(PY) viewer/generate_manifest.py

list: ## Показать доступные сценарии
	@test -x $(PY) || { echo "✗ venv не создан. Запустите: make init"; exit 1; }
	@$(PY) viewer/viewer.py --list

info: ## Информация о системе
	@echo "OS:      $$(uname -a)"
	@echo "Python:  $$(python3 --version 2>&1)"
	@echo "Display: $${DISPLAY:-<no display>}"
	@echo "CWD:     $$(pwd)"
	@echo "Repo:    $$(git rev-parse --show-toplevel 2>/dev/null || echo '<not git>')"

clean-cache: ## Удалить кеш скачанных картинок
	@rm -rf viewer/cache/*
	@echo "✓ viewer/cache/ очищен"

clean: clean-cache ## Полная очистка (cache + venv + __pycache__)
	@rm -rf $(VENV)
	@rm -rf viewer/__pycache__
	@echo "✓ venv и __pycache__ удалены"
