import motor.motor_asyncio
from datetime import datetime, timezone
from app.config import MONGODB_URI, MONGODB_DB

# Single client reused across requests
_client: motor.motor_asyncio.AsyncIOMotorClient = None


def get_client() -> motor.motor_asyncio.AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
    return _client


def get_db():
    return get_client()[MONGODB_DB]


async def save_enquiry(data: dict) -> str:
    """
    Save enquiry to MongoDB.
    Returns the inserted document ID as string.
    """
    db = get_db()
    collection = db["enquiries"]

    doc = {
        **data,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await collection.insert_one(doc)
    return str(result.inserted_id)


async def ping_db() -> bool:
    """Health check — returns True if MongoDB is reachable."""
    try:
        await get_client().admin.command("ping")
        return True
    except Exception:
        return False
