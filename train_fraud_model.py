import pandas as pd
from pymongo import MongoClient
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
import joblib
from datetime import datetime

# ----------------------------
# MongoDB connection
# ----------------------------
client = MongoClient("mongodb://localhost:27017/")
db = client["upi_fraud_db"]

# ----------------------------
# Load data
# ----------------------------
transactions = pd.DataFrame(list(db.transactions.find()))
flagged = pd.DataFrame(list(db.flagged_transactions.find()))

if transactions.empty:
    raise Exception("No transactions found in MongoDB!")

# ----------------------------
# Merge with fraud labels
# ----------------------------
# Create a column 'is_fraud' (1 = fraud, 0 = legit)
transactions["is_fraud"] = transactions["_id"].isin(flagged["_id"]).astype(int)

# ----------------------------
# Feature engineering
# ----------------------------
def extract_features(df):
    # Convert timestamp to datetime
    df["time"] = pd.to_datetime(df.get("time", datetime.utcnow()), errors="coerce")
    df["hour"] = df["time"].dt.hour
    df["day_of_week"] = df["time"].dt.dayofweek

    # Encode device
    df["device"] = df.get("device", "Unknown")
    le_device = LabelEncoder()
    df["device_enc"] = le_device.fit_transform(df["device"])

    # Amount (ensure numeric)
    df["amount"] = pd.to_numeric(df.get("amount", 0), errors="coerce").fillna(0)

    # Example: could add sender history features later
    return df[["amount", "hour", "day_of_week", "device_enc"]], le_device

X, le_device = extract_features(transactions)
y = transactions["is_fraud"]

# ----------------------------
# Train-test split
# ----------------------------
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ----------------------------
# Train model
# ----------------------------
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# ----------------------------
# Evaluate
# ----------------------------
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))

# ----------------------------
# Save model and encoder
# ----------------------------
joblib.dump(model, "fraud_model.pkl")
joblib.dump(le_device, "device_encoder.pkl")
print("✅ Model and encoder saved!")
