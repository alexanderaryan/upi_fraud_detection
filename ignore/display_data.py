from pymongo import MongoClient
import pandas as pd
import matplotlib.pyplot as plt

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["upi_fraud_db"]
flagged = db["flagged_transactions"]

# Load flagged transactions into DataFrame
data = list(flagged.find({}))
df = pd.DataFrame(data)

# Convert time to datetime
df["time"] = pd.to_datetime(df["time"])

# Extract hour, date
df["hour"] = df["time"].dt.hour
df["date"] = df["time"].dt.date

# Show quick summary
print("🔍 Total Flagged Records:", len(df))
print(df.head(3))

# ==========================
# 📊 1. Frequency of Fraud by Hour
# ==========================
plt.figure(figsize=(10, 4))
df["hour"].value_counts().sort_index().plot(kind='bar', color='tomato')
plt.title("Fraudulent Transactions by Hour")
plt.xlabel("Hour of Day")
plt.ylabel("Number of Transactions")
plt.grid(True, axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig("fraud_by_hour.png")
plt.show()

# ==========================
# 📊 2. Fraud by City (if 'city' field exists)
# ==========================
if "city" in df.columns:
    plt.figure(figsize=(10, 4))
    df["city"].value_counts().plot(kind='bar', color='steelblue')
    plt.title("Fraudulent Transactions by City")
    plt.xlabel("City")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig("fraud_by_city.png")
    plt.show()

# ==========================
# 📊 3. Fraud by Device
# ==========================
if "device" in df.columns:
    plt.figure(figsize=(8, 4))
    df["device"].value_counts().plot(kind='bar', color='mediumseagreen')
    plt.title("Fraudulent Transactions by Device")
    plt.xlabel("Device")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig("fraud_by_device.png")
    plt.show()


# ==========================
# 💾 4. Export to CSV and Excel
# ==========================
df.to_csv("flagged_transactions.csv", index=False)
df.to_excel("flagged_transactions.xlsx", index=False)
print("✅ Exported to flagged_transactions.csv and .xlsx")
