"""Server-rendered web UI: routes, templates and static files."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from todo_server.config import Settings
from todo_server.web.routes import router

WEB_DIR = Path(__file__).parent


def mount_web(app: FastAPI, settings: Settings) -> None:
    templates = Jinja2Templates(directory=WEB_DIR / "templates")
    templates.env.globals["settings"] = settings
    app.state.templates = templates
    app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")
    app.include_router(router)


__all__ = ["mount_web"]
