from faker import Faker
import pandas as pd
import random
from datetime import datetime, timedelta

fake = Faker()
Faker.seed(0)
random.seed(0)

def generate_transaction():
    sender = fake.email()
    receiver = fake.email()
    amount = round(random.uniform(10, 100000), 2)
    txn_time = fake.date_time_between(start_date='-30d', end_date='now')
    location = fake.city()
    device = random.choice(['Android', 'iOS', 'Windows', 'Linux'])

    # Simple fraud logic:
    # Flag as fraud if amount > ₹50,000 between 12 AM - 5 AM
    is_night = txn_time.hour < 5
    is_fraud = amount > 50000 and is_night

    return {
        "txn_id": fake.uuid4(),
        "sender": sender,
        "receiver": receiver,
        "amount": amount,
        "time": txn_time.strftime("%Y-%m-%d %H:%M:%S"),
        "location": location,
        "device": device,
        "is_fraud": is_fraud
    }

# Generate dataset
def generate_transactions(n=500):
    return [generate_transaction() for _ in range(n)]

# Save to CSV or use with Mongo later
if __name__ == "__main__":
    data = generate_transactions(500)
    df = pd.DataFrame(data)
    df.to_csv("upi_transactions.csv", index=False)
    print("✅ 500 transactions generated and saved to 'upi_transactions.csv'")