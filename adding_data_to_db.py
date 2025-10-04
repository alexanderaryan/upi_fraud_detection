# mongo_setup.py
import pandas as pd
from pymongo import MongoClient
from datetime import datetime

# --------------------------
# MongoDB Connection
# --------------------------
client = MongoClient("mongodb://localhost:27017/")
db = client["upi_fraud_db"]

# --------------------------
# 1️⃣ Create collections
# --------------------------
collections = ["transactions", "flagged_transactions", "blocked_senders", "users"]
for col_name in collections:
    if col_name not in db.list_collection_names():
        db.create_collection(col_name)
        print(f"✅ Collection '{col_name}' created.")
    else:
        print(f"ℹ️ Collection '{col_name}' already exists.")

# --------------------------
# 2️⃣ Create indexes (if needed)
# --------------------------
# Ensure blocked_senders has unique index on upi_id
db.blocked_senders.create_index("upi_id", unique=True)
print("✅ Index created on 'blocked_senders.upi_id'")

# Optional: add indexes for transactions
db.transactions.create_index("sender")
db.transactions.create_index("receiver")
db.transactions.create_index("time")

# --------------------------
# 3️⃣ Insert sample data (optional)
# --------------------------
csv_file = "upi_transactions.csv"  # Your CSV file path
try:
    df = pd.read_csv(csv_file)
    if not df.empty:
        records = df.to_dict(orient="records")
        db.transactions.insert_many(records)
        print(f"✅ {len(records)} records inserted into 'transactions'")
    else:
        print("⚠️ CSV file is empty. No data inserted.")
except FileNotFoundError:
    print(f"⚠️ CSV file '{csv_file}' not found. Skipping data insert.")

# --------------------------
# 4️⃣ Sample blocked_senders data (optional)
# --------------------------
# This is just for demo / testing
sample_blocked = [
    {"upi_id": "scam@upi", "reason": "High transaction amount", "blocked_at": datetime.utcnow()},
    {"upi_id": "fraud123@okaxis", "reason": "Transaction during odd hours", "blocked_at": datetime.utcnow()},
]
for entry in sample_blocked:
    db.blocked_senders.update_one(
        {"upi_id": entry["upi_id"]},
        {"$set": entry},
        upsert=True
    )
print("✅ Sample blocked_senders inserted/updated")

print("🎉 MongoDB setup completed!")
