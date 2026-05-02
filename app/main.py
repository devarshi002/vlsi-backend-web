import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import ALLOWED_ORIGINS
from app.routers.enquiry import router as enquiry_router

# ── Logging ─────────────────────────────────────────────────
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
    description="Handles enquiry forms, lead storage, and email alerts.",
    version="1.0.0",
    docs_url="/docs",       # Swagger UI  →  /docs
    redoc_url="/redoc",     # ReDoc UI    →  /redoc
)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── Routes ───────────────────────────────────────────────────
app.include_router(enquiry_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "project": "NanoCore VLSI Backend",
        "status":  "running",
        "docs":    "/docs",
    }
