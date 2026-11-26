"""Operational endpoints: health and version."""

from fastapi import APIRouter, Request

router = APIRouter(tags=["system"])


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/version")
def version(request: Request) -> dict[str, str]:
    settings = request.app.state.settings
    return {"version": settings.version, "channel": settings.channel}
