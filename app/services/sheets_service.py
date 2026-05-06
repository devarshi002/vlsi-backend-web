import logging
import os
from datetime import datetime, timezone

from app.config import GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_FILE

logger = logging.getLogger(__name__)

# Column headers for the Google Sheet
HEADERS = [
    "Timestamp", "Source", "Name", "Phone",
    "Email", "Course", "Mode", "Message"
]


def _get_service():
    """
    Build and return the Google Sheets API service client.
    Returns None if credentials file is missing (graceful fallback).
    """
    if not GOOGLE_SHEET_ID:
        logger.warning("GOOGLE_SHEET_ID not set — skipping Sheets write")
        return None

    if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
        logger.warning(
            f"Google credentials file '{GOOGLE_CREDENTIALS_FILE}' not found — "
            "skipping Sheets write. See .env.example for setup instructions."
        )
        return None

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = service_account.Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_FILE, scopes=scopes
        )
        return build("sheets", "v4", credentials=creds, cache_discovery=False)
    except Exception as e:
        logger.error(f"Failed to build Google Sheets service: {e}")
        return None


def _ensure_header_row(service) -> None:
    """Write header row if the sheet is empty."""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=GOOGLE_SHEET_ID,
            range="Sheet1!A1:H1"
        ).execute()

        if not result.get("values"):
            service.spreadsheets().values().update(
                spreadsheetId=GOOGLE_SHEET_ID,
                range="Sheet1!A1",
                valueInputOption="RAW",
                body={"values": [HEADERS]}
            ).execute()
            logger.info("Header row written to Google Sheet")
    except Exception as e:
        logger.error(f"Could not check/write header row: {e}")


def append_to_sheet(data: dict) -> bool:
    """
    Append one enquiry row to Google Sheets.
    Returns True on success, False on failure (non-blocking).
    """
    service = _get_service()
    if not service:
        return False

    try:
        _ensure_header_row(service)

        timestamp = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
        row = [
            timestamp,
            data.get("source", ""),
            data.get("name", ""),
            data.get("phone", ""),
            data.get("email", ""),
            data.get("course", ""),
            data.get("mode", ""),
            data.get("message", ""),
        ]

        service.spreadsheets().values().append(
            spreadsheetId=GOOGLE_SHEET_ID,
            range="Sheet1!A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]}
        ).execute()

        logger.info(f"Row appended to Google Sheet for {data.get('name')}")
        return True

    except Exception as e:
        logger.error(f"Google Sheets append failed: {e}")
        return False