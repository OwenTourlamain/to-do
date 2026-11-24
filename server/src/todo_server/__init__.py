def main() -> None:
    import uvicorn

    from todo_server.app import create_app
    from todo_server.config import load_settings

    settings = load_settings()
    uvicorn.run(create_app(settings), host=settings.host, port=settings.port, workers=1)
