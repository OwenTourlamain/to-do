# todo-server

The self-hosted server: web UI, API and integrations.

```sh
uv sync
uv run todo-server        # http://127.0.0.1:8000
uv run pytest
uv run ruff check && uv run ruff format --check
```

Configuration is by environment variable; see `.env.example`.
