import logging
import time
from typing import Any, Callable
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import Receive, Scope, Send

from app.api import chat, documents, health, widget
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import request_id_var, setup_logging
from app.core.db import Base, engine
from app.models import bot_token as _
from app.api.sites import router as sites_router
from pathlib import Path
from fastapi.responses import FileResponse


Base.metadata.create_all(bind=engine)


settings = get_settings()
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)
app.include_router(health.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(sites_router)

widget_app = FastAPI()
widget_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],

)
widget_app.include_router(widget.router)
WIDGET_JS = Path(__file__).parent / "static" / "widget.js"
app.mount("/widget", widget_app)

class DshboardCORS(CORSMiddleware):
    """Same as CORSMiddleware, but leaves /widget/* to the widget app's own open CORS."""
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"].startswith("/widget/"):
            await self.app(scope,receive,send)
            return
        await super().__call__(scope, receive, send)

app.add_middleware(
    DshboardCORS,
    allow_origins=settings.cors_list,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


def error_response(status_code: int, error: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": error, "message": message, "request_id": request_id_var.get()},
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = uuid.uuid4().hex[:12]
    request_id_var.set(request_id)
    start = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        # full traceback goes to the log only, never to the client
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        response = error_response(500, "InternalError", "Something went wrong.")

    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "%s %s -> %d (%.0f ms)", request.method, request.url.path, response.status_code, elapsed_ms
    )
    return response


@widget_app.exception_handler(AppError)
async def widget_app_error(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": type(exc).__name__, "message": exc.message},
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    # report which fields are wrong, never the values the user sent
    fields = dict.fromkeys(
        ".".join(str(p) for p in e["loc"] if p != "body") or "request" for e in exc.errors()
    )
    return error_response(422, "ValidationError", f"Invalid request: {', '.join(fields)}.")


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(request: Request, exc: StarletteHTTPException):
    return error_response(exc.status_code, "HTTPError", str(exc.detail))


@app.get("/widget.js", include_in_schema=False)
def serve_widget():
    return FileResponse(WIDGET_JS, media_type="application/javascript")


logger.info("App started in %s mode", settings.env)