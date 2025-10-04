# retrain_model.py
import pandas as pd
from pymongo import MongoClient
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,  # Could also be DEBUG for more detail
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()  # Log to console
    ]
)

logger = logging.getLogger("UPIFraudDetection")

client = MongoClient("mongodb://localhost:27017/")
db = client["upi_fraud_db"]

MODEL_PATH = "fraud_model.pkl"
ENCODER_PATH = "device_encoder.pkl"


def retrain_model():
    logger.info("🔄 Retraining ML model with latest transactions...")

    transactions = pd.DataFrame(list(db.transactions.find()))
    flagged = pd.DataFrame(list(db.flagged_transactions.find()))

    if transactions.empty:
        logger.info("⚠️ No transactions found.")
        return

    # Merge with fraud labels
    transactions["is_fraud"] = transactions["_id"].isin(flagged["_id"]).astype(int)

    # Feature engineering
    transactions["time"] = pd.to_datetime(transactions.get("time", datetime.utcnow()), errors="coerce")
    transactions["hour"] = transactions["time"].dt.hour
    transactions["day_of_week"] = transactions["time"].dt.dayofweek

    transactions["device"] = transactions.get("device", "Unknown")
    le_device = LabelEncoder()
    transactions["device_enc"] = le_device.fit_transform(transactions["device"])

    X = transactions[["amount", "hour", "day_of_week", "device_enc"]]
    y = transactions["is_fraud"]

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Save model & encoder
    joblib.dump(model, MODEL_PATH)
    joblib.dump(le_device, ENCODER_PATH)
    logger.info("✅ Model retrained and saved!")
