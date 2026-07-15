import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Explicit UTC timestamps in every log line (ASVS V16.2.2).
logging.Formatter.converter = time.gmtime
logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(name)s %(message)s")

from app.core.config import settings  # noqa: E402
from app.routers import gauge, health, health_profile, home, preferences, rank, recommend, search  # noqa: E402

logger = logging.getLogger("main_service")

app = FastAPI(title="Main Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Never leak stack traces / internals to the client (A10) — log server-side, return a generic message.
    logger.exception("unhandled error handling %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."})


app.include_router(health.router)
app.include_router(home.router)
app.include_router(health_profile.router)
app.include_router(preferences.router)
app.include_router(gauge.router)
app.include_router(recommend.router)
app.include_router(search.router)
app.include_router(rank.router)
