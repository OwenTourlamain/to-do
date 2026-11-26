"""Web UI routes."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from todo_server.clock import utc_now

router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return request.app.state.templates.TemplateResponse(request, "index.html")


@router.get("/hello", response_class=HTMLResponse)
def hello(request: Request) -> HTMLResponse:
    now = utc_now().astimezone(request.app.state.settings.timezone)
    return request.app.state.templates.TemplateResponse(request, "_hello.html", {"now": now})
