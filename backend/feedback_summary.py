import os
from datetime import datetime, timedelta
from pymongo import MongoClient
from .email_service import EmailService

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.environ.get("MONGO_DB", "choicepilot")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

async def send_daily_feedback_summary():
    """Summarize feedback from the last 24 hours and email it."""
    since = datetime.utcnow() - timedelta(days=1)
    feedback = list(db.decision_feedback.find({"timestamp": {"$gte": since}}))
    if not feedback:
        return

    helpful = sum(1 for f in feedback if f.get("helpful"))
    not_helpful = len(feedback) - helpful
    comments = [f.get("feedback_text") for f in feedback if f.get("feedback_text")]

    summary_lines = [
        f"Total feedback: {len(feedback)}",
        f"Helpful: {helpful}",
        f"Not Helpful: {not_helpful}",
    ]
    if comments:
        summary_lines.append("Comments:\n" + "\n".join(f"- {c}" for c in comments[:10]))

    email_service = EmailService()
    await email_service._send_email(
        ADMIN_EMAIL,
        "Daily Feedback Summary",
        "<pre>" + "\n".join(summary_lines) + "</pre>"
    )
