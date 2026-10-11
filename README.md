# tracked-artifacts-check

Проверяет, что в git-индексе репозитория (`git ls-files`) не лежат файлы, которым там не место: `.env` и ключи, `node_modules`, `__pycache__`, `dist/`, логи, архивы, бинарники и файлы крупнее порога. Работает офлайн, только читает индекс, без зависимостей, Python 3.10+.

## Быстрый старт

```bash
python -m tracked_artifacts                  # текущий репозиторий
python -m tracked_artifacts . --large-mb 1   # порог крупного файла 1 МиБ
python -m tracked_artifacts . --json
python -m tracked_artifacts . --allow "tests/fixtures/*"   # исключить намеренно закоммиченные файлы
```

Пример вывода:

```text
[ERROR] secret-file: .env (matches .env)
[ERROR] dependency-dir: node_modules/left-pad/index.js (matches node_modules/*)
2 tracked artifact(s) found in 120 files
```

## Категории

| Категория | Примеры |
| --- | --- |
| `secret-file` | `.env`, `.env.production`, `*.pem`, `*.key`, `id_rsa`, `*.p12` |
| `dependency-dir` | `node_modules/`, `.venv/`, `venv/` |
| `build-output` | `__pycache__/`, `*.pyc`, `dist/`, `build/`, `*.egg-info/` |
| `os-junk` | `.DS_Store`, `Thumbs.db` |
| `log-file`, `archive`, `binary` | `*.log`, `*.zip`, `*.tar.gz`, `*.exe`, `*.dll` |
| `large-file` | любой файл не меньше порога (по умолчанию 5 МиБ) |

Шаблоны вида `.env.example`, `.env.sample`, `.env.template` разрешены.

## Коды возврата

`0` — артефактов нет, `1` — найдены, `2` — путь не git-репозиторий или git недоступен.

## Ограничения

- Проверяет только текущий индекс, а не историю коммитов: уже закоммиченный и удалённый секрет остаётся в истории. Для него нужна очистка истории и ротация ключа.
- Список правил фиксированный; свои правила пока не поддерживаются.

## Использование в CI

```yaml
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- name: tracked-artifacts-check
  run: python -m tracked_artifacts .
```

## Разработка

```bash
python -m unittest discover -s tests -t .
```

## Лицензия

MIT — см. [LICENSE](LICENSE).
