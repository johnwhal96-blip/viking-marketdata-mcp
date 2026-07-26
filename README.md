# Viking Market Data MCP

MVP MCP-сервера поверх WebSocket API `bot.fkviking.com`.

Сервер решает две основные задачи:

1. показывает портфели, доступные текущей роли Viking;
2. выгружает историю выбранного портфеля за заданный период.

Для небольших результатов `get_portfolio_data` возвращает строки непосредственно
в `structuredContent`. Для больших результатов сервер создаёт CSV и возвращает
временную подписанную ссылку. Запрос `delivery=inline` может быть автоматически
переключён на файл, если ответ превышает серверные лимиты.

## MCP tools

### `list_available_portfolios`

Параметры:

- `history_only=false` — вернуть все доступные портфели;
- `history_only=true` — вернуть только портфели с включённой записью истории.

Результат содержит:

- `robot_id`;
- `portfolio`;
- `owner`;
- `history_available`.

### `get_portfolio_data`

Обязательные параметры:

- `robot_id`;
- `portfolio`;
- `date_from` — ISO 8601 с часовым поясом;
- `date_to` — ISO 8601 с часовым поясом.

Необязательные параметры:

- `fields` — по умолчанию `buy`, `sell`, `pos`;
- `aggregation` — `raw`, `10s`, `1m`, `5m`, `10m`, `1h`, `6h`, `24h`;
- `delivery` — `auto`, `inline`, `file`, `stream`, `summary`;
- `preview_rows` — от 0 до 100.

## 1. Локальный запуск через stdio

Требуется Python 3.11+ и `uv`.

```bash
cp .env.example .env
```

Заполните в `.env`:

```dotenv
VIKING_EMAIL=...
VIKING_API_KEY=...
VIKING_ROLE=trader
```

Установите зависимости и запустите тесты:

```bash
uv sync --dev
uv run pytest
```

Запуск MCP:

```bash
uv run python -m app.main --transport stdio
```

Пример настройки Codex:

```toml
[mcp_servers.viking_marketdata_local]
command = "uv"
args = ["run", "--directory", "/absolute/path/viking-marketdata-mcp", "python", "-m", "app.main", "--transport", "stdio"]
startup_timeout_sec = 20
tool_timeout_sec = 300
```

## 2. Локальный запуск через HTTP

Сгенерируйте отдельный токен:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Добавьте его в `.env` как `MCP_ACCESS_TOKEN`, затем:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Проверка:

```bash
curl http://127.0.0.1:8000/health
```

MCP endpoint:

```text
http://127.0.0.1:8000/mcp
```

## 3. Деплой в Railway

Проект содержит `Dockerfile` и `railway.json`.

Переменные Railway:

```dotenv
VIKING_EMAIL=...
VIKING_API_KEY=...
VIKING_ROLE=trader
VIKING_WS_URL=wss://bot.fkviking.com/ws
MCP_ACCESS_TOKEN=...
EXPORT_DIR=/data/exports
INLINE_MAX_ROWS=500
INLINE_MAX_BYTES=200000
MAX_POINTS_PER_FIELD=500000
EXPORT_TTL_SECONDS=86400
VIKING_REQUEST_TIMEOUT_SECONDS=45
```

В Railway нужно:

1. создать сервис из репозитория или выполнить `railway up`;
2. добавить перечисленные переменные;
3. добавить Volume с mount path `/data`;
4. создать публичный домен;
5. дождаться успешной проверки `/health`.

После выдачи домена MCP URL будет иметь вид:

```text
https://YOUR-DOMAIN.up.railway.app/mcp
```

Настройка Codex:

```bash
export VIKING_MCP_TOKEN="тот же MCP_ACCESS_TOKEN"
```

```toml
[mcp_servers.viking_marketdata]
url = "https://YOUR-DOMAIN.up.railway.app/mcp"
bearer_token_env_var = "VIKING_MCP_TOKEN"
tool_timeout_sec = 300
```

Проверьте:

```bash
codex mcp list
```

В интерфейсе Codex используйте `/mcp`.

## 4. Примеры запросов

```text
Покажи доступные мне портфели и отметь, у каких включена история.
```

```text
Скачай buy, sell и pos по портфелю demo робота 1
за период с 2026-07-25T10:00:00+03:00 по 2026-07-25T11:00:00+03:00.
Используй агрегацию 1m.
```

```text
Покажи первые строки истории buy и sell по портфелю demo за последний час.
Если данных много, верни CSV.
```

## Безопасность

- Viking API key хранится только в переменных окружения.
- Remote MCP закрыт Bearer-токеном `MCP_ACCESS_TOKEN`.
- CSV-ссылки подписаны, ограничены по времени и не содержат API key.
- `/health` не раскрывает значения секретов.
- Сервер предоставляет только read-only tools.

## Ограничения MVP

- Поддерживается история полей портфеля, а не сделок и заявок.
- `stream` принимается как значение контракта, но в MVP преобразуется в CSV.
- Для файла используется локальный диск/Volume Railway, а не S3.
- При превышении `MAX_POINTS_PER_FIELD` нужно укрупнить агрегацию или сократить период.

