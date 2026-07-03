# Code Auditor

AI-аудитор кода: анализ безопасности, качества и архитектуры в одной CLI-утилите.

Объединяет 6 статических анализаторов (bandit, radon, vulture, pylint, semgrep, pip-audit) с LLM-анализом для поиска уязвимостей, архитектурных проблем и нарушений качества кода. Генерирует структурированные отчёты в JSON/Markdown/HTML с маппингом OWASP Top 10.

## Возможности

- **Аудит безопасности** — SQL-инъекции, XSS, хардкод-секреты, слабая криптография, path traversal, SSRF, небезопасная десериализация (OWASP Top 10)
- **Качество кода** — цикломатическая сложность, индекс поддерживаемости, God objects, нарушения SOLID, мёртвый код, дублирование
- **Сканирование зависимостей** — известные CVE через pip-audit
- **AI-глубокий анализ** — LLM-ревью архитектуры и неочевидных уязвимостей
- **Мультипровайдерный LLM** — OpenAI, Anthropic Claude, DeepSeek, Groq, локальный Ollama через LiteLLM
- **Структурированные отчёты** — JSON, Markdown, интерактивный HTML с фильтрами
- **Плагинная архитектура** — добавляйте свои анализаторы через протокол `Analyzer`

## Быстрый старт

### Требования

- Python 3.10+
- pip

### Установка

```bash
# Клонируем репозиторий
git clone https://github.com/todkavodka/basis_tech2.git
cd basis_tech2

# Создаём виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate

# Устанавливаем со всеми зависимостями анализаторов
pip install -e ".[analyzers]"

# Dev-зависимости (опционально, для тестов)
pip install -e ".[dev]"
```

### Проверка

```bash
code-auditor --help
code-auditor list-analyzers
```

## Использование

### Базовое сканирование

```bash
# Сканирование проекта (все анализаторы, без AI)
code-auditor scan ./my-project --no-ai

# Полное сканирование с AI-анализом
code-auditor scan ./my-project
```

### Опции

```
code-auditor scan <путь> [ОПЦИИ]

Аргументы:
  ПУТЬ                            Путь к директории проекта

Опции:
  -a, --analyzer TEXT             Анализаторы для запуска. Повторяется.
                                  [bandit|radon|vulture|pylint|semgrep|pip-audit|ai|all]
                                  По умолчанию: all
  -o, --output TEXT               Путь к файлу отчёта (.json, .md, .html)
  -f, --format TEXT               Формат: json, markdown, html, both, all
                                  [по умолчанию: markdown]
  -s, --severity TEXT             Минимальная серьёзность: critical, high, medium, low, info
                                  [по умолчанию: info]
  -m, --model TEXT                Модель LLM для AI-анализа
                                  [по умолчанию: из конфига или openai/gpt-4o]
  --no-ai                         Пропустить AI-анализ (офлайн)
  -v, --verbose                   Подробный вывод
  -c, --config TEXT               Путь к файлу конфигурации
  --help                          Показать справку
```

### Примеры

```bash
# Только анализаторы безопасности
code-auditor scan ./src -a bandit -a semgrep --no-ai

# Полный скан, сохранить JSON + Markdown + HTML
code-auditor scan ./src -o audit-report -f all

# Фильтр: только high и critical
code-auditor scan ./src -s high --no-ai

# Использовать Claude вместо GPT-4o
code-auditor scan ./src -m anthropic/claude-sonnet-4-20250514

# Локальный Ollama (без API-ключа)
code-auditor scan ./src -m ollama/llama3

# Подробный вывод
code-auditor scan ./src -v --no-ai
```

## Настройка AI

AI-анализ требует API-ключ для выбранного провайдера.

### DeepSeek (рекомендуется)

```bash
export DEEPSEEK_API_KEY=sk-ваш-ключ
code-auditor scan ./src -m deepseek/deepseek-chat
```

### OpenAI

```bash
export OPENAI_API_KEY=sk-ваш-ключ
code-auditor scan ./src
```

### Anthropic Claude

```bash
export ANTHROPIC_API_KEY=sk-ant-ваш-ключ
code-auditor scan ./src -m anthropic/claude-sonnet-4-20250514
```

### Ollama (локальный, бесплатно)

```bash
# 1. Установите Ollama: https://ollama.com
# 2. Скачайте модель
ollama pull llama3

# 3. Запускайте (API-ключ не нужен)
code-auditor scan ./src -m ollama/llama3
```

### Офлайн (без LLM)

```bash
code-auditor scan ./src --no-ai
```

## Конфигурация

Code Auditor читает конфигурацию из `.code-auditor.toml` или `[tool.code-auditor]` в `pyproject.toml`.

### Быстрая наставка

```bash
cp .code-auditor.example.toml .code-auditor.toml
# Отредактируйте .code-auditor.toml — вставьте ваш API-ключ
```

### Файл конфигурации (`.code-auditor.toml`)

```toml
[llm]
# Поддерживаемые: openai/gpt-4o, openai/o3-mini, anthropic/claude-sonnet-4-20250514,
#                 ollama/llama3, deepseek/deepseek-chat, groq/llama-3.1-70b-versatile
model = "deepseek/deepseek-chat"
temperature = 0.1       # 0.0 = детерминированно, 1.0 = креативно
max_tokens = 4096       # Макс. токенов за ответ
api_key = "sk-ваш-ключ" # Перекрывает переменную окружения
# api_base = "http://localhost:11434"  # Для Ollama, прокси и т.д.

[analyzers]
# Пропустить определённые анализаторы
skip = []

[report]
format = "markdown"     # json, markdown, html, both, all
severity_threshold = "info"  # critical, high, medium, low, info
max_file_size_kb = 500  # Макс. размер файла для LLM
```

### Конфиг через `pyproject.toml`

```toml
[tool.code-auditor.llm]
model = "anthropic/claude-sonnet-4-20250514"
temperature = 0.0

[tool.code-auditor.analyzers]
skip = ["semgrep"]

[tool.code-auditor.report]
format = "both"
severity_threshold = "medium"
```

### Готовые конфиги

#### DeepSeek (замените только ключ)

```toml
# .code-auditor.toml
[llm]
model = "deepseek/deepseek-chat"
api_key = "sk-ваш-ключ-здесь"
temperature = 0.1
max_tokens = 4096
```

#### OpenAI

```toml
[llm]
model = "openai/gpt-4o"
api_key = "sk-ваш-ключ-здесь"
```

#### Anthropic Claude

```toml
[llm]
model = "anthropic/claude-sonnet-4-20250514"
api_key = "sk-ant-ваш-ключ-здесь"
```

#### Groq (быстрый, бесплатный тир)

```toml
[llm]
model = "groq/llama-3.1-70b-versatile"
api_key = "gsk_ваш-ключ-здесь"
```

#### Ollama (локальный, без ключа)

```toml
[llm]
model = "ollama/llama3"
api_base = "http://localhost:11434"
```

### Приоритет конфигурации

1. Аргументы CLI (наивысший приоритет)
2. `.code-auditor.toml` в корне проекта
3. `[tool.code-auditor]` в `pyproject.toml`
4. Значения по умолчанию

### Поддерживаемые LLM-провайдеры

| Провайдер | Строка модели | Env-переменная для ключа |
|-----------|--------------|--------------------------|
| OpenAI | `openai/gpt-4o`, `openai/o3-mini` | `OPENAI_API_KEY` |
| Anthropic | `anthropic/claude-sonnet-4-20250514` | `ANTHROPIC_API_KEY` |
| DeepSeek | `deepseek/deepseek-chat` | `DEEPSEEK_API_KEY` |
| Groq | `groq/llama-3.1-70b-versatile` | `GROQ_API_KEY` |
| Ollama (локальный) | `ollama/llama3`, `ollama/codellama` | (не нужен) |

## Анализаторы

| Анализатор | Тип | Что находит |
|-----------|-----|-------------|
| **bandit** | Безопасность | SQL-инъекции, XSS, хардкод-секреты, слабая криптография, command injection |
| **radon** | Сложность | Цикломатическая сложность, индекс поддерживаемости, метрики Halstead |
| **vulture** | Мёртвый код | Неиспользуемые функции, классы, импорты, переменные |
| **pylint** | Качество | God objects (R0902/R0904), нарушения SOLID (R0901), дублирование (R0801) |
| **semgrep** | Безопасность | Taint-анализ, паттерн-based поиск уязвимостей |
| **pip-audit** | Зависимости | Известные CVE в Python-пакетах |
| **ai** | Глубокий анализ | Ревью архитектуры, неочевидные уязвимости, паттерны проектирования |

### Маппинг OWASP Top 10

| OWASP | Категория | Определяется |
|-------|-----------|-------------|
| A02 | Сбои криптографии | bandit (B3xx, B5xx) |
| A03 | Инъекции (SQL, XSS, CMD) | bandit (B6xx, B7xx), semgrep |
| A05 | Некорректная конфигурация | bandit (B201, B612) |
| A06 | Уязвимые компоненты | pip-audit |
| A07 | Сбои аутентификации | bandit (B105-B107) |
| A08 | Сбои целостности | bandit (B301, B506) |
| A09 | Логирование и мониторинг | bandit (B110, B112) |

## Форматы отчётов

### Вывод в терминал

```
Code Auditor v0.1.0
Target: /home/user/my-project

   Audit Summary
┏━━━━━━━━━━┳━━━━━━━┓
┃ Severity ┃ Count ┃
┡━━━━━━━━━━╇━━━━━━━┩
│ High     │     3 │
│ Medium   │    12 │
│ Low      │    28 │
│ Info     │    15 │
└──────────┴───────┘

Total: 58 findings from 6 tools

Top findings:

  [    HIGH] bandit/B605 — Starting a process with a shell...
           at /home/user/my-project/app.py:42
```

### JSON-отчёт

```json
{
  "metadata": {
    "tool_version": "0.1.0",
    "target": "/home/user/my-project",
    "timestamp": "2026-07-03T12:00:00+00:00",
    "tools_used": ["bandit", "radon", "vulture", "pylint", "semgrep", "pip-audit"]
  },
  "summary": {
    "total_findings": 58,
    "by_severity": { "high": 3, "medium": 12, "low": 28, "info": 15 },
    "by_category": { "security": 8, "quality": 20, "complexity": 15, "dead_code": 12, "dependency": 3 },
    "by_owasp": { "A03": 5, "A02": 2, "A07": 1 }
  },
  "findings": [...]
}
```

### HTML-отчёт

Интерактивный отчёт с фильтрами по severity, tool, category и поиском по сообщениям. Колонки сортируются по клику.

```bash
code-auditor scan ./src -o report -f html
# Откроется файл report.html
```

## Коды выхода

| Код | Значение |
|-----|----------|
| 0 | Нет критических или высоких находок |
| 1 | Обнаружены находки уровня high |
| 2 | Обнаружены находки уровня critical |

Используйте в CI/CD для прерывания сборки при проблемах безопасности:

```bash
code-auditor scan ./src --no-ai -s high || exit 1
```

## Интеграция с CI/CD

### GitHub Actions

```yaml
name: Code Audit
on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e ".[analyzers]"
      - run: code-auditor scan . --no-ai -o audit-report -f all
      - uses: actions/upload-artifact@v4
        with:
          name: audit-report
          path: audit-report.*
```

### GitLab CI

```yaml
code-audit:
  image: python:3.12
  script:
    - pip install -e ".[analyzers]"
    - code-auditor scan . --no-ai -o audit-report -f all
  artifacts:
    paths:
      - audit-report.*
```

## Архитектура

### Схема работы

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI (Typer)                             │
│                    cli.py → config.py                           │
└──────────────────────┬──────────────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          │     Реестр анализаторов  │
          │      registry.py        │
          └────────────┬────────────┘
                       │
    ┌──────────┬───────┼───────┬──────────┬──────────┐
    ▼          ▼       ▼       ▼          ▼          ▼
 bandit     radon   vulture  pylint    semgrep   pip-audit
 (безоп.)  (слож.) (мёртв.) (качеств.) (taint)  (зависим.)
    │          │       │       │          │          │
    └──────────┴───────┴───────┴──────────┴──────────┘
                       │
              Нормализованные Findings
              (модели Pydantic)
                       │
          ┌────────────┴────────────┐
          │     Генераторы отчётов   │
          │  JSON │ Markdown │ HTML  │
          └─────────────────────────┘
```

**AI-анализ** параллельно со статическими анализаторами отправляет код в LLM через LiteLLM:

```
┌──────────────┐      ┌──────────────────────────────────┐
│ AI Analyzer  │─────▶│ LiteLLM (мультипровайдер)         │
│ ai_analyzer  │      │  OpenAI / Claude / DeepSeek /     │
│              │◀─────│  Groq / Ollama                    │
└──────────────┘      └──────────────────────────────────┘
```

### Поток данных

1. **CLI** парсит аргументы, загружает конфиг из `.code-auditor.toml` или `pyproject.toml`
2. **Реестр** перебирает выбранные анализаторы (каждый — плагин)
3. Каждый **анализатор** запускает свой инструмент через `subprocess`, парсит вывод, нормализует в модель `Finding`
4. **AI-анализатор** собирает Python-файлы, отправляет в LLM с промптами безопасности/архитектуры
5. Все находки объединяются, фильтруются по серьёзности, оборачиваются в `Report`
6. **Генераторы отчётов** сериализуют в JSON/Markdown/HTML

### Ключевые дизайн-решения

| Решение | Выбор | Обоснование |
|---------|-------|-------------|
| Плагинная система | Protocol-based (`Analyzer`) | Нулевая связанность — добавляйте анализаторы без изменения ядра |
| Поиск инструментов | `find_tool()` проверяет venv bin, затем PATH | Работает в venv без изменения PATH |
| Каскад конфигов | CLI > `.code-auditor.toml` > `pyproject.toml` > дефолты | Гибкость без сложности |
| Абстракция LLM | LiteLLM | Одно API, 100+ провайдеров, без привязки к вендору |
| Модели данных | Pydantic v2 | Валидация, сериализация, структурированный вывод |
| Форматы отчётов | JSON + Markdown + HTML | Машиночитаемый + человекочитаемый + интерактивный |

## Структура проекта

```
code-auditor/
├── .code-auditor.example.toml         # Пример конфигурации
├── pyproject.toml                     # Конфиг пакета + зависимости
├── src/code_auditor/
│   ├── cli.py                         # Typer CLI: scan, list-analyzers
│   ├── config.py                      # Загрузчик конфигов (.toml / pyproject)
│   ├── models.py                      # Pydantic: Finding, Report, Summary
│   ├── registry.py                    # Реестр плагинов-анализаторов
│   ├── analyzers/
│   │   ├── base.py                    # Протокол Analyzer + find_tool()
│   │   ├── bandit_analyzer.py         # Безопасность → маппинг OWASP
│   │   ├── radon_analyzer.py          # CC, индекс поддерживаемости
│   │   ├── vulture_analyzer.py        # Мёртвый код (с confidence)
│   │   ├── pylint_analyzer.py         # SOLID, God objects, дублирование
│   │   ├── semgrep_analyzer.py        # Taint/pattern-анализ
│   │   ├── pip_audit_analyzer.py      # CVE зависимостей (OWASP A06)
│   │   └── ai_analyzer.py            # Глубокий LLM-анализ
│   ├── llm/
│   │   ├── provider.py               # Обёртка LiteLLM (5 провайдеров)
│   │   └── prompts.py                # Промпты безопасности и архитектуры
│   └── reports/
│       ├── json_report.py            # JSON-вывод
│       ├── markdown_report.py        # Markdown с таблицами
│       └── html_report.py            # Интерактивный HTML с фильтрами
└── tests/
    ├── test_models.py                # Тесты моделей
    ├── test_analyzers.py             # Интеграционные тесты анализаторов
    └── test_cli.py                   # Тесты CLI-команд
```

## Добавление своих анализаторов

Реализуйте протокол `Analyzer`:

```python
# src/code_auditor/analyzers/my_analyzer.py
from pathlib import Path
from code_auditor.analyzers.base import Analyzer
from code_auditor.models import Finding, Category, Severity

class MyAnalyzer:
    name = "my-analyzer"

    def analyze(self, path: Path) -> list[Finding]:
        # Запустите ваш инструмент, распарсите вывод
        return [Finding(
            tool=self.name,
            rule_id="MY-001",
            severity=Severity.MEDIUM,
            category=Category.QUALITY,
            file="example.py",
            line=10,
            message="Найдена проблема",
        )]
```

Зарегистрируйте в `registry.py`:

```python
from code_auditor.analyzers.my_analyzer import MyAnalyzer
register(MyAnalyzer())
```

## Разработка

```bash
# Установить dev-зависимости
pip install -e ".[analyzers,dev]"

# Запустить тесты
pytest tests/ -v

# Тесты с покрытием
pytest tests/ -v --cov=code_auditor --cov-report=term-missing
```

## Лицензия

MIT
