from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api import api_router_v1

def create_app():
    app = FastAPI()
    app.include_router(api_router_v1)
    app.mount(f"{api_router_v1.prefix}/static", StaticFiles(directory="static"), name="static")
    app.mount(f"{api_router_v1.prefix}/media", StaticFiles(directory="media"), name="media")
    return app

__all__ = ["create_app"]