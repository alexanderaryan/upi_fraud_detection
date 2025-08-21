from pymongo import MongoClient
from datetime import datetime, timedelta
import pandas as pd

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["upi_fraud_db"]
collection = db["transactions"]
flagged = db["flagged_transactions"]

# 🔄 Clean up flagged_transactions collection (optional: for dev/testing)
flagged.delete_many({})

# ✅ Rule 1 – High amount during night hours (00:00–05:00)
night_fraud = collection.find({
    "amount": { "$gt": 50000 },
    "$expr": { "$lt": [ { "$hour": { "$toDate": "$time" } }, 5 ] }
})
for txn in night_fraud:
    txn["fraud_reason"] = "High amount during night hours"
    txn_copy = txn.copy()
    txn_copy.pop("_id", None)
    flagged.insert_one(txn_copy)

# ✅ Rule 2 – More than 5 transactions to same receiver in 5 minutes
pipeline = [
    { "$group": {
        "_id": { "receiver": "$receiver", "minute": { "$substr": ["$time", 0, 16] } },
        "count": { "$sum": 1 },
        "txns": { "$push": "$$ROOT" }
    }},
    { "$match": { "count": { "$gt": 5 } }}
]
results = collection.aggregate(pipeline)
for group in results:
    for txn in group["txns"]:
        txn["fraud_reason"] = "More than 5 txns to same receiver in 5 minutes"
        txn_copy = txn.copy()
        txn_copy.pop("_id", None)
        flagged.insert_one(txn_copy)

# ✅ Rule 3 – Same sender and receiver repeating multiple times in 1 day
pipeline = [
    { "$addFields": {
        "day": { "$substr": ["$time", 0, 10] }
    }},
    { "$group": {
        "_id": {
            "sender": "$sender",
            "receiver": "$receiver",
            "day": "$day"
        },
        "count": { "$sum": 1 },
        "txns": { "$push": "$$ROOT" }
    }},
    { "$match": { "count": { "$gt": 3 } }}
]
results = collection.aggregate(pipeline)
for group in results:
    for txn in group["txns"]:
        txn["fraud_reason"] = "Repeated sender-receiver pair in 1 day"
        txn_copy = txn.copy()
        txn_copy.pop("_id", None)
        flagged.insert_one(txn_copy)

# ✅ Rule 4 – Suspicious devices used at night
night_devices = collection.find({
    "device": { "$in": ["Linux", "Windows"] },
    "$expr": { "$lt": [ { "$hour": { "$toDate": "$time" } }, 5 ] }
})
for txn in night_devices:
    txn["fraud_reason"] = "Suspicious device used at night"
    txn_copy = txn.copy()
    txn_copy.pop("_id", None)
    flagged.insert_one(txn_copy)

# ✅ Rule 5 – High frequency of transactions in short time span by one sender
pipeline = [
    { "$addFields": {
        "minute": { "$substr": ["$time", 0, 16] }
    }},
    { "$group": {
        "_id": { "sender": "$sender", "minute": "$minute" },
        "count": { "$sum": 1 },
        "txns": { "$push": "$$ROOT" }
    }},
    { "$match": { "count": { "$gt": 5 } }}
]
results = collection.aggregate(pipeline)
for group in results:
    for txn in group["txns"]:
        txn["fraud_reason"] = "High frequency by sender in 1 minute"
        txn_copy = txn.copy()
        txn_copy.pop("_id", None)
        flagged.insert_one(txn_copy)

# ✅ Final summary
print("📊 Total transactions:", collection.count_documents({}))
print("🚨 Total suspicious transactions flagged:", flagged.count_documents({}))
