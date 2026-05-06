import httpx
import logging
import os
from datetime import datetime, timezone

from app.config import ALERT_EMAIL

logger = logging.getLogger(__name__)

BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
SENDER_EMAIL  = "devarshitambulkar2@gmail.com"  # Brevo verified sender
SENDER_NAME   = "NanoCore VLSI"


def _build_html(data: dict, form_type: str) -> str:
    source_label = "📋 Scroll Popup" if form_type == "popup" else "📬 Contact Page"
    timestamp = datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M %p UTC")

    rows = ""
    field_labels = {
        "name":    "Full Name",
        "phone":   "Phone",
        "email":   "Email",
        "course":  "Course Interest",
        "mode":    "Preferred Mode",
        "message": "Message",
        "source":  "Source",
    }

    for key, label in field_labels.items():
        value = data.get(key)
        if value:
            rows += f"""
            <tr>
              <td style="padding:8px 12px;font-weight:600;color:#a78bfa;
                background:#0d1f3c;border-bottom:1px solid #1e3a5f;
                width:140px;white-space:nowrap;">{label}</td>
              <td style="padding:8px 12px;color:#e2e8f0;
                background:#0a1628;border-bottom:1px solid #1e3a5f;">{value}</td>
            </tr>"""

    return f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0;padding:0;background:#050a1a;font-family:'Segoe UI',sans-serif;">
      <div style="max-width:560px;margin:30px auto;border-radius:12px;overflow:hidden;
        border:1px solid #1e3a5f;box-shadow:0 20px 60px rgba(0,0,0,0.6);">

        <!-- Header -->
        <div style="background:linear-gradient(135deg,#5b21b6,#16a34a);padding:20px 28px;">
          <div style="font-size:11px;letter-spacing:3px;color:rgba(255,255,255,0.7);
            text-transform:uppercase;margin-bottom:4px;">NanoCore VLSI Institute</div>
          <div style="font-size:20px;font-weight:700;color:#fff;">🔔 New Lead — {source_label}</div>
          <div style="font-size:11px;color:rgba(255,255,255,0.5);margin-top:4px;">{timestamp}</div>
        </div>

        <!-- Table -->
        <table style="width:100%;border-collapse:collapse;">
          {rows}
        </table>

        <!-- Footer -->
        <div style="background:#0d1f3c;padding:14px 20px;text-align:center;
          font-size:11px;color:#475569;border-top:1px solid #1e3a5f;">
          This alert was sent automatically by NanoCore backend · Do not reply
        </div>
      </div>
    </body>
    </html>
    """


async def send_alert_email(data: dict, form_type: str = "popup") -> bool:
    """
    Async email via Brevo HTTP API — no SMTP, works on Render free plan.
    300 emails/day free, no recipient restrictions.
    """
    if not BREVO_API_KEY:
        logger.error("❌ BREVO_API_KEY not set on Render")
        return False

    subject_map = {
        "popup":   "🚀 New Popup Lead",
        "contact": "📬 New Contact Form Submission",
    }
    subject = f"{subject_map.get(form_type, '📩 New Enquiry')} — {data.get('name', 'Unknown')}"

    payload = {
        "sender": {
            "name":  SENDER_NAME,
            "email": SENDER_EMAIL,
        },
        "to": [{"email": ALERT_EMAIL}],
        "subject": subject,
        "htmlContent": _build_html(data, form_type),
    }

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://api.brevo.com/v3/smtp/email",
                json=payload,
                headers={
                    "api-key":      BREVO_API_KEY,
                    "Content-Type": "application/json",
                },
                timeout=15,
            )

        if res.status_code == 201:
            logger.info(f"✅ Email sent for {data.get('name')} [{form_type}]")
            return True
        else:
            logger.error(f"❌ Brevo error {res.status_code}: {res.text}")
            return False

    except Exception as e:
        logger.error(f"❌ Email failed: {e}", exc_info=True)
        return False