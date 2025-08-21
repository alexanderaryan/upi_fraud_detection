import pandas as pd
from pymongo import MongoClient

# Connect to local MongoDB (Docker runs on localhost)
client = MongoClient("mongodb://localhost:27017/")
db = client["upi_fraud_db"]
collection = db["transactions"]

# Load your CSV
df = pd.read_csv("upi_transactions.csv")

# Convert to dictionary format and insert
records = df.to_dict(orient="records")
collection.insert_many(records)

print("✅ Data inserted successfully into MongoDB!")
