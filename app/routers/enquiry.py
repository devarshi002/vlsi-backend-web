import asyncio
import logging
from fastapi import APIRouter, Request, BackgroundTasks
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.enquiry import PopupEnquiry, ContactEnquiry, EnquiryResponse
from app.services.database import save_enquiry
from app.services.email_service import send_alert_email
from app.services.sheets_service import append_to_sheet

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Enquiry"])
limiter = Limiter(key_func=get_remote_address)


async def run_side_effects(data: dict, form_type: str):
    """Run email (async) and sheets (sync in thread pool) as background tasks."""
    logger.info(f"[side_effects] Starting for {data.get('name')} via {form_type}")

    # ✅ Email — properly awaited now (async function)
    try:
        email_ok = await send_alert_email(data, form_type)
        logger.info(f"[side_effects] Email: {'✅ sent' if email_ok else '❌ failed'}")
    except Exception as e:
        logger.error(f"[side_effects] Email crashed: {e}", exc_info=True)

    # ✅ Sheets — sync library, run in thread pool so it doesn't block event loop
    try:
        sheets_ok = await asyncio.get_event_loop().run_in_executor(
            None, append_to_sheet, data
        )
        logger.info(f"[side_effects] Sheets: {'✅ appended' if sheets_ok else '❌ failed'}")
    except Exception as e:
        logger.error(f"[side_effects] Sheets crashed: {e}", exc_info=True)


# ── Popup form ──────────────────────────────────────────────

@router.post("/enquiry/popup", response_model=EnquiryResponse)
@limiter.limit("5/minute")
async def popup_enquiry(
    request: Request,
    body: PopupEnquiry,
    background_tasks: BackgroundTasks
):
    try:
        data = body.model_dump()
        logger.info(f"[popup] Received from {data.get('name')} — {data.get('phone')}")

        # Save to MongoDB
        doc_id = await save_enquiry(data)
        logger.info(f"[popup] Saved to MongoDB: {doc_id}")

        # Add email + sheets as proper FastAPI background task
        background_tasks.add_task(run_side_effects, data, "popup")

        return EnquiryResponse(
            success=True,
            message="Thanks! Our counsellor will reach out within 4 hours."
        )

    except Exception as e:
        logger.error(f"[popup] Error: {e}", exc_info=True)
        return EnquiryResponse(
            success=False,
            message="Something went wrong. Please try again or call us directly."
        )


# ── Contact page form ───────────────────────────────────────

@router.post("/enquiry/contact", response_model=EnquiryResponse)
@limiter.limit("3/minute")
async def contact_enquiry(
    request: Request,
    body: ContactEnquiry,
    background_tasks: BackgroundTasks
):
    try:
        data = body.model_dump()
        logger.info(f"[contact] Received from {data.get('name')} — {data.get('email')}")

        # Save to MongoDB
        doc_id = await save_enquiry(data)
        logger.info(f"[contact] Saved to MongoDB: {doc_id}")

        # Add email + sheets as proper FastAPI background task
        background_tasks.add_task(run_side_effects, data, "contact")

        return EnquiryResponse(
            success=True,
            message="Message received! We'll get back to you within 4 business hours."
        )

    except Exception as e:
        logger.error(f"[contact] Error: {e}", exc_info=True)
        return EnquiryResponse(
            success=False,
            message="Something went wrong. Please try again or call us directly."
        )


# ── Health check ────────────────────────────────────────────

@router.get("/health")
async def health():
    from app.services.database import ping_db
    db_ok = await ping_db()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
    }