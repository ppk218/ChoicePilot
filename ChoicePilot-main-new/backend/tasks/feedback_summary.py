import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")

client = AsyncIOMotorClient(MONGO_URL) if MONGO_URL else None
db = client[DB_NAME] if client and DB_NAME else None


async def aggregate_feedback() -> None:
    """Aggregate feedback from the last 24 hours and store summary."""
    if db is None:
        print("Database not configured")
        return

    period_start = datetime.utcnow() - timedelta(days=1)
    pipeline = [
        {"$match": {"timestamp": {"$gte": period_start}}},
        {"$group": {"_id": "$helpful", "count": {"$sum": 1}}},
    ]

    results = await db.decision_feedback.aggregate(pipeline).to_list(length=10)
    total = sum(r["count"] for r in results)
    helpful = next((r["count"] for r in results if r["_id"]), 0)
    unhelpful = next((r["count"] for r in results if not r["_id"]), 0)

    summary = {
        "period_start": period_start,
        "period_end": datetime.utcnow(),
        "total_feedback": total,
        "helpful_count": helpful,
        "unhelpful_count": unhelpful,
        "helpfulness_rate": helpful / total if total else 0.0,
        "generated_at": datetime.utcnow(),
        # TODO: Use AI to generate a natural language summary once API keys are active
    }

    await db.feedback_summaries.insert_one(summary)


async def scheduler() -> None:
    """Run feedback aggregation on a fixed interval."""
    interval = int(os.environ.get("FEEDBACK_SUMMARY_INTERVAL", 24 * 60 * 60))
    while True:
        try:
            await aggregate_feedback()
        except Exception as e:  # pragma: no cover - simple logging
            print(f"Error aggregating feedback: {e}")
        await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(scheduler())
