from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.middlewares import *
from app.api import api_router_v1
from app.db.mongodb import connect_to_mongo, close_mongo_connection


def create_app():
    app = FastAPI()
    # 中间件
    add_cors_middleware(app)
    add_trace_middleware(app)
    # add_exception_handler(app)
    add_logging_middleware(app)
    # 通过 api_router 注册所有子路由
    app.include_router(api_router_v1)
    app.mount(f"{api_router_v1.prefix}/media", StaticFiles(directory="media"), name="media")

    # MongoDB连接生命周期
    @app.on_event("startup")
    async def startup_event():
        await connect_to_mongo()

    @app.on_event("shutdown")
    async def shutdown_event():
        await close_mongo_connection()

    return app


__all__ = ["create_app"]