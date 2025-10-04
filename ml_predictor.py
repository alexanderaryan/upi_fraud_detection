import joblib
import pandas as pd
from datetime import datetime

# Load trained model
model = joblib.load("fraud_model.pkl")
device_encoder = joblib.load("device_encoder.pkl")


def predict_fraud_ml(transaction: dict) -> bool:
    """
    Predict if a transaction is fraudulent using ML model.

    transaction: dict with keys: sender, receiver, amount, device, timestamp
    Returns: True if fraud, False otherwise
    """
    # Convert timestamp to datetime
    dt = datetime.fromisoformat(transaction.get("timestamp", datetime.utcnow().isoformat()))
    hour = dt.hour
    day_of_week = dt.weekday()

    # Device encoding
    device = transaction.get("device", "Unknown")
    try:
        device_enc = device_encoder.transform([device])[0]
    except ValueError:
        # Unknown device not seen during training
        device_enc = -1

    # Amount
    amount = float(transaction.get("amount", 0))

    # Prepare features
    df = pd.DataFrame([{
        "amount": amount,
        "hour": hour,
        "day_of_week": day_of_week,
        "device_enc": device_enc
    }])

    pred = model.predict(df)[0]
    return bool(pred)
