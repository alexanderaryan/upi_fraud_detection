
from pymongo import MongoClient
from datetime import datetime

# Connect to local MongoDB (change if using cloud MongoDB)
client = MongoClient("mongodb://localhost:27017/")
db = client["upi_fraud_db"]
blocked_senders = db["blocked_senders"]

def block_sender(upi_id: str, reason="fraudulent transaction"):
    """Insert or update a blocked sender in MongoDB."""
    blocked_senders.update_one(
        {"upi_id": upi_id},
        {"$set": {"reason": reason, "blocked_at": datetime.utcnow()}},
        upsert=True
    )
    print(f"Sender {upi_id} blocked.")

def is_sender_blocked(upi_id: str) -> bool:
    """Check if a sender is already blocked in MongoDB."""
    return blocked_senders.find_one({"upi_id": upi_id}) is not None
