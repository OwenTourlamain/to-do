"""Application factory: wires settings, the database, the API and the web UI together."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from todo_server.api import system_router
from todo_server.clock import utc_now
from todo_server.config import Settings, load_settings
from todo_server.db import Database
from todo_server.services.bootstrap import ensure_default_user
from todo_server.web import mount_web


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        database = Database(settings.database_url)
        database.migrate()
        with database.unit_of_work() as uow:
            ensure_default_user(uow, now=utc_now(), timezone=settings.timezone.key)
        app.state.db = database
        try:
            yield
        finally:
            database.close()

    app = FastAPI(title="todo-server", version=settings.version, lifespan=lifespan)
    app.state.settings = settings
    app.include_router(system_router)
    mount_web(app, settings)
    return app
