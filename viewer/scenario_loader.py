"""
Парсер scenarios.js → dict.

Сценарии хранятся в docs/js/scenarios.js как JS-литерал объекта.
Парсер рассчитан на стабильный формат этого проекта:
  - одинарные кавычки для строк
  - ключи объектов без кавычек
  - числовые, булевы значения, null
  - поддержка trailing commas в массивах/объектах
  - поддержка UTF-8 (русский текст)
"""
import json
import re
from pathlib import Path


def parse_scenarios_js(path):
    """Прочитать SCENARIOS из JS-файла и вернуть как dict.

    Бросает ValueError, если SCENARIOS не найден.
    """
    text = Path(path).read_text(encoding="utf-8")

    m = re.search(r"const\s+SCENARIOS\s*=\s*\{", text)
    if not m:
        raise ValueError(f"SCENARIOS const not found in {path}")

    # Brace-match с учётом строк в одинарных/двойных кавычках
    start = m.end() - 1
    depth = 0
    end = start
    in_str = False
    quote = None
    i = start
    while i < len(text):
        c = text[i]
        if in_str:
            if c == "\\" and i + 1 < len(text):
                i += 2
                continue
            if c == quote:
                in_str = False
        else:
            if c == "'" or c == '"':
                in_str = True
                quote = c
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        i += 1
    else:
        raise ValueError("Unbalanced braces in SCENARIOS object")

    obj = text[start:end + 1]

    obj = _add_quotes_to_unquoted_keys(obj)
    obj = _single_to_double_quotes(obj)
    obj = _strip_trailing_commas(obj)

    return json.loads(obj)


def _add_quotes_to_unquoted_keys(obj):
    """Обернуть в кавычки ключи объектов вида `key:` после `{` или `,`."""
    return re.sub(
        r"([{,]\s*)([A-Za-z_][\w]*)(\s*:)",
        r'\1"\2"\3',
        obj,
    )


def _single_to_double_quotes(obj):
    """Заменить '...' на "...". Не обрабатывает \' внутри строк (не используется)."""
    return re.sub(r"'([^']*)'", r'"\1"', obj)


def _strip_trailing_commas(obj):
    """Удалить trailing commas перед ] или } (валидно в JS, невалидно в JSON)."""
    return re.sub(r",(\s*[\]}])", r"\1", obj)


def list_scenarios(scenarios):
    """Удобный список (id, name) для CLI/логов."""
    return [(sid, s.get("name", sid)) for sid, s in scenarios.items()]
