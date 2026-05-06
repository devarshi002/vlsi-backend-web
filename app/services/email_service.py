import httpx
import logging
import os
from datetime import datetime, timezone

from app.config import ALERT_EMAIL

logger = logging.getLogger(__name__)

BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
SENDER_EMAIL  = "devarshitambulkar2@gmail.com"  # Brevo verified sender
SENDER_NAME   = "NanoCore VLSI Institute"


def _build_owner_html(data: dict, form_type: str) -> str:
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
        <div style="background:linear-gradient(135deg,#5b21b6,#16a34a);padding:20px 28px;">
          <div style="font-size:11px;letter-spacing:3px;color:rgba(255,255,255,0.7);
            text-transform:uppercase;margin-bottom:4px;">NanoCore VLSI Institute</div>
          <div style="font-size:20px;font-weight:700;color:#fff;">🔔 New Lead — {source_label}</div>
          <div style="font-size:11px;color:rgba(255,255,255,0.5);margin-top:4px;">{timestamp}</div>
        </div>
        <table style="width:100%;border-collapse:collapse;">{rows}</table>
        <div style="background:#0d1f3c;padding:14px 20px;text-align:center;
          font-size:11px;color:#475569;border-top:1px solid #1e3a5f;">
          This alert was sent automatically by NanoCore backend · Do not reply
        </div>
      </div>
    </body>
    </html>
    """


def _build_student_html(data: dict) -> str:
    name = data.get("name", "Student")
    course = data.get("course", "")

    return f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0;padding:0;background:#050a1a;font-family:'Segoe UI',sans-serif;">
      <div style="max-width:560px;margin:30px auto;border-radius:12px;overflow:hidden;
        border:1px solid #1e3a5f;box-shadow:0 20px 60px rgba(0,0,0,0.6);">

        <!-- Header -->
        <div style="background:linear-gradient(135deg,#5b21b6,#16a34a);padding:24px 28px;">
          <div style="font-size:11px;letter-spacing:3px;color:rgba(255,255,255,0.7);
            text-transform:uppercase;margin-bottom:4px;">NanoCore VLSI Institute</div>
          <div style="font-size:22px;font-weight:700;color:#fff;">Thank You, {name}! 🎉</div>
          <div style="font-size:12px;color:rgba(255,255,255,0.6);margin-top:6px;">
            Your enquiry has been received successfully
          </div>
        </div>

        <!-- Body -->
        <div style="background:#0a1628;padding:28px;">
          <p style="color:#e2e8f0;font-size:15px;line-height:1.7;margin:0 0 16px;">
            Dear <strong style="color:#a78bfa;">{name}</strong>,
          </p>
          <p style="color:#cbd5e1;font-size:14px;line-height:1.7;margin:0 0 16px;">
            Thank you for your interest in <strong style="color:#a78bfa;">NanoCore VLSI Institute</strong>. 
            We have received your enquiry{f" regarding <strong style='color:#a78bfa;'>{course}</strong>" if course else ""} 
            and our counsellor will get in touch with you within <strong style="color:#34d399;">4 hours</strong>.
          </p>

          <!-- Info Box -->
          <div style="background:#0d1f3c;border:1px solid #1e3a5f;border-radius:8px;padding:16px;margin:20px 0;">
            <p style="color:#94a3b8;font-size:13px;margin:0 0 8px;">What happens next?</p>
            <p style="color:#e2e8f0;font-size:13px;margin:4px 0;">✅ Our team will review your enquiry</p>
            <p style="color:#e2e8f0;font-size:13px;margin:4px 0;">📞 A counsellor will call you within 4 hours</p>
            <p style="color:#e2e8f0;font-size:13px;margin:4px 0;">🎓 We'll guide you to the best course for you</p>
          </div>

          <p style="color:#cbd5e1;font-size:13px;line-height:1.7;margin:16px 0 0;">
            If you have any urgent queries, feel free to reach out to us directly.
          </p>
        </div>

        <!-- Footer -->
        <div style="background:#0d1f3c;padding:16px 20px;text-align:center;
          border-top:1px solid #1e3a5f;">
          <p style="color:#475569;font-size:11px;margin:0;">
            NanoCore VLSI Institute · This is an automated confirmation email
          </p>
        </div>

      </div>
    </body>
    </html>
    """


async def _send_single_email(to_email: str, subject: str, html: str) -> bool:
    """Send one email via Brevo API."""
    payload = {
        "sender": {
            "name":  SENDER_NAME,
            "email": SENDER_EMAIL,
        },
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html,
    }

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

    return res.status_code == 201


async def send_alert_email(data: dict, form_type: str = "popup") -> bool:
    """
    Send 2 emails:
    1. Owner — lead alert with full details
    2. Student — confirmation email
    """
    if not BREVO_API_KEY:
        logger.error("❌ BREVO_API_KEY not set on Render")
        return False

    subject_map = {
        "popup":   "🚀 New Popup Lead",
        "contact": "📬 New Contact Form Submission",
    }
    owner_subject   = f"{subject_map.get(form_type, '📩 New Enquiry')} — {data.get('name', 'Unknown')}"
    student_subject = "✅ We received your enquiry — NanoCore VLSI Institute"

    student_email = data.get("email")
    success = True

    # 1. Email to Owner
    try:
        ok = await _send_single_email(
            to_email=ALERT_EMAIL,
            subject=owner_subject,
            html=_build_owner_html(data, form_type),
        )
        if ok:
            logger.info(f"✅ Owner alert sent for {data.get('name')} [{form_type}]")
        else:
            logger.error(f"❌ Owner alert failed for {data.get('name')}")
            success = False
    except Exception as e:
        logger.error(f"❌ Owner email crashed: {e}", exc_info=True)
        success = False

    # 2. Confirmation Email to Student (only if email provided)
    if student_email:
        try:
            ok = await _send_single_email(
                to_email=student_email,
                subject=student_subject,
                html=_build_student_html(data),
            )
            if ok:
                logger.info(f"✅ Student confirmation sent to {student_email}")
            else:
                logger.error(f"❌ Student confirmation failed for {student_email}")
        except Exception as e:
            logger.error(f"❌ Student email crashed: {e}", exc_info=True)

    return success