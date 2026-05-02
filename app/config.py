from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URI          = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB           = os.getenv("MONGODB_DB", "nanocore")

SMTP_EMAIL           = os.getenv("SMTP_EMAIL", "demo@gmail.com")
SMTP_PASSWORD        = os.getenv("SMTP_PASSWORD", "demo-password")
ALERT_EMAIL          = os.getenv("ALERT_EMAIL", "admin@nanocore.in")

GOOGLE_SHEET_ID      = os.getenv("GOOGLE_SHEET_ID", "")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

ALLOWED_ORIGINS      = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000"
).split(",")
