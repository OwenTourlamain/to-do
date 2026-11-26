"""FastAPI application: a hello-world page plus health and version endpoints."""

from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from todo_server.config import Settings, load_settings

PACKAGE_DIR = Path(__file__).parent


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(title="todo-server", version=settings.version)
    templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")
    templates.env.globals["settings"] = settings
    app.mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static")

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "index.html")

    @app.get("/hello", response_class=HTMLResponse)
    def hello(request: Request) -> HTMLResponse:
        now = datetime.now(UTC).astimezone(settings.timezone)
        return templates.TemplateResponse(request, "_hello.html", {"now": now})

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/version")
    def version() -> dict[str, str]:
        return {"version": settings.version, "channel": settings.channel}

    return app
