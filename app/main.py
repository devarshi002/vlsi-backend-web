import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import ALLOWED_ORIGINS, SMTP_EMAIL, ALERT_EMAIL
from app.routers.enquiry import router as enquiry_router

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Rate limiter ─────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["100/hour"])

# ── App ──────────────────────────────────────────────────────
app = FastAPI(
    title="NanoCore VLSI — Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS — must be added BEFORE rate limiter middleware ───────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,   # must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Attach rate limiter AFTER cors
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── Routes ───────────────────────────────────────────────────
app.include_router(enquiry_router)


@app.get("/", tags=["Root"])
@app.head("/", tags=["Root"])
async def root():
    return {
        "project": "NanoCore VLSI Backend",
        "status":  "running",
        "docs":    "/docs",
    }


@app.on_event("startup")
async def startup_event():
    logger.info("=== NanoCore Backend Starting ===")
    logger.info(f"SMTP_EMAIL    : {SMTP_EMAIL}")
    logger.info(f"ALERT_EMAIL   : {ALERT_EMAIL}")

    from app.services.database import ping_db
    db_ok = await ping_db()
    logger.info(f"MongoDB       : {'CONNECTED' if db_ok else 'FAILED'}")