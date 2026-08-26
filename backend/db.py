from motor.motor_asyncio import AsyncIOMotorClient

from config import MONGODB_URI, MONGODB_DB

_client: AsyncIOMotorClient | None = None

def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGODB_URI)
    return _client


def get_database():
    client = get_client()
    return client[MONGODB_DB]


def get_users_collection():
    db = get_database()
    return db["users"]


def get_repositories_collection():
    db = get_database()
    return db["repositories"]


def get_analysis_results_collection():
    db = get_database()
    return db["analysis_results"]


def get_generated_docs_collection():
    db = get_database()
    return db["generated_docs"]


def get_commit_history_collection():
    db = get_database()
    return db["commit_history"]
