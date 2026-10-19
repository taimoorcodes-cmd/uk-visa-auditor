"""All settings in one place. Values come from your .env file."""
import os
from dotenv import load_dotenv
load_dotenv()

def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "data", "auditor.db"))
VIDEO_URL = os.getenv("VIDEO_URL", "https://assets.mixkit.co/videos/preview/mixkit-aerial-view-of-the-city-of-london-34588-large.mp4")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
CHAT_MODEL = os.getenv("CHAT_MODEL", "openrouter/auto")
FALLBACK_MODELS = [m.strip() for m in os.getenv("FALLBACK_MODELS", "").split(",") if m.strip()]
VISION_MODEL = os.getenv("VISION_MODEL", "")
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = _int("SMTP_PORT", 587)
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "") or SMTP_USER
DEV_SHOW_CODE = os.getenv("DEV_SHOW_CODE", "0") == "1"
OTP_MINUTES = 10
OTP_MAX_TRIES = 5
OTP_RESEND_SECONDS = 60
FREE_LIMITS = {"audit": _int("FREE_AUDITS_PER_MONTH", 3), "screenshot": _int("FREE_SCREENSHOTS_PER_MONTH", 5), "interview": _int("FREE_INTERVIEW_PER_MONTH", 10)}
PRO_PRICE_PKR = _int("PRO_PRICE_PKR", 1500)
PRO_DAYS = _int("PRO_DAYS", 30)
PAY_ACCOUNT_NAME = os.getenv("PAY_ACCOUNT_NAME", "")
PAY_EASYPAISA_NUMBER = os.getenv("PAY_EASYPAISA_NUMBER", "")
PAY_JAZZCASH_NUMBER = os.getenv("PAY_JAZZCASH_NUMBER", "")
ADMIN_EMAILS = [e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()]
SAFEPAY_PUBLIC_KEY = os.getenv("SAFEPAY_PUBLIC_KEY", "")
SAFEPAY_ENV = os.getenv("SAFEPAY_ENV", "sandbox")
LINKS = {"student_visa": "https://www.gov.uk/student-visa", "money": "https://www.gov.uk/student-visa/money", "documents": "https://www.gov.uk/student-visa/documents-you-must-provide", "english": "https://www.gov.uk/student-visa/knowledge-of-english", "tb": "https://www.gov.uk/tb-test-visa", "apply": "https://www.gov.uk/student-visa/apply"}
TB_VALID_DAYS = 183
IELTS_VALID_DAYS = 730
REFERENCE_MAX_AGE_DAYS = 365
ENGLISH_LEVELS = {"B2": 5.5, "B1": 4.0}
