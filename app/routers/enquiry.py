import asyncio
import logging
from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.enquiry import PopupEnquiry, ContactEnquiry, EnquiryResponse
from app.services.database import save_enquiry
from app.services.email_service import send_alert_email
from app.services.sheets_service import append_to_sheet

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Enquiry"])
limiter = Limiter(key_func=get_remote_address)


def _run_side_effects(data: dict, form_type: str):
    """
    Fire email + sheets in background threads so the API
    responds immediately without waiting for SMTP / Sheets API.
    """
    loop = asyncio.get_event_loop()

    # Email alert
    loop.run_in_executor(None, send_alert_email, data, form_type)

    # Google Sheets
    loop.run_in_executor(None, append_to_sheet, data)


# ── Popup form ──────────────────────────────────────────────────────────────

@router.post("/enquiry/popup", response_model=EnquiryResponse)
@limiter.limit("5/minute")          # max 5 submissions per IP per minute
async def popup_enquiry(request: Request, body: PopupEnquiry):
    """
    Handles the scroll-triggered popup form.
    Rate limited: 5 requests / minute per IP.
    """
    try:
        data = body.model_dump()

        # 1 — Save to MongoDB
        doc_id = await save_enquiry(data)
        logger.info(f"[popup] Saved MongoDB doc {doc_id} for {data['name']}")

        # 2 — Email + Sheets (background, non-blocking)
        _run_side_effects(data, "popup")

        return EnquiryResponse(
            success=True,
            message="Thanks! Our counsellor will reach out within 4 hours."
        )

    except Exception as e:
        logger.error(f"[popup] Unexpected error: {e}")
        return EnquiryResponse(
            success=False,
            message="Something went wrong. Please try again or call us directly."
        )


# ── Contact page form ───────────────────────────────────────────────────────

@router.post("/enquiry/contact", response_model=EnquiryResponse)
@limiter.limit("3/minute")          # stricter — full form, less spammable
async def contact_enquiry(request: Request, body: ContactEnquiry):
    """
    Handles the full contact page form.
    Rate limited: 3 requests / minute per IP.
    """
    try:
        data = body.model_dump()

        # 1 — Save to MongoDB
        doc_id = await save_enquiry(data)
        logger.info(f"[contact] Saved MongoDB doc {doc_id} for {data['name']}")

        # 2 — Email + Sheets (background, non-blocking)
        _run_side_effects(data, "contact")

        return EnquiryResponse(
            success=True,
            message="Message received! We'll get back to you within 4 business hours."
        )

    except Exception as e:
        logger.error(f"[contact] Unexpected error: {e}")
        return EnquiryResponse(
            success=False,
            message="Something went wrong. Please try again or call us directly."
        )


# ── Health check ────────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    from app.services.database import ping_db
    db_ok = await ping_db()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
    }
