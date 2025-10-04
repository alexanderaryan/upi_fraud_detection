---

# 💸 UPI Fraud Detection

A web-based fraud detection system that helps identify fraudulent UPI transactions in real time.
This project combines **Flask, MongoDB, and Machine Learning** to simulate transaction checks, flag suspicious activity, and provide an admin dashboard with analytics and visualizations.

---

## ✨ Features

* 🛡️ **Rule-based fraud detection** (odd hours, high amounts, blacklisted UPI IDs, etc.)
* 📊 **Interactive dashboard** with charts (daily/hourly/device analysis using Chart.js)
* 📝 **User authentication** with role-based access (admin vs user)
* 🚀 **REST API** for real-time fraud checks (`/api/check`)
* 🤖 **ML-powered fraud scoring** (Logistic Regression + periodic retraining)
* 📑 **Transaction history** with pagination and search

---

## ⚙️ Tech Stack

**Backend**: Python, Flask
**Database**: MongoDB (via Docker)
**Frontend**: HTML, Jinja2, Chart.js, CSS
**Extras**: Faker (for fake transactions), bcrypt (secure password hashing), scikit-learn (ML), joblib (model persistence)

---

## 📂 Project Structure

```
FraudUPIProject/
│
├── app.py                   # Flask app & REST API
├── ml_predictor.py          # ML model training + prediction
├── adding_data_to_db.py     # One-time MongoDB setup script
├── insert_sample_data.py    # Add fake/sample UPI transactions
├── ml_predictor.py          # Validate ML predictions
├── block_sender_db.py       # To block sender while detected of Fraud
├── fake_data.py             # To generate fake UPI data
├── retrain_model.py         # To retrain model after every new 500 transactions recorded in DB
├── train_fraud_model.py     # To Train the ML model with data from DB
│
├── static/                  # CSS, JS, Chart.js assets
├── templates/               # Jinja2 HTML templates
│
├── upi_transactions.csv     # Sample dataset
│
├── fraud_model.pkl          # Trained ML model (auto-generated)
├── device_encoder.pkl       # Encoded device labels (auto-generated)
│
├── requirements.txt
└── README.md
```

---

## 🚀 Setup & Run

### 1️⃣ Clone & Install

```bash
git clone https://github.com/alexanderaryan/upi_fraud_detection.git
cd upi_fraud_detection
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ Start MongoDB (Docker)

```bash
docker run -d -p 27017:27017 --name mongodb mongo
```

### 3️⃣ Initialize Database and train ML Model

```bash
python fake_data.py 
python adding_data_to_db.py
python train_fraud_model.py
```

### 4️⃣ Run the Flask App

```bash
python app.py
```

App will run at 👉 `http://127.0.0.1:5000`

---

## 📡 API Usage

### 🔹 Fraud Check Endpoint

`POST /api/check`

**Request:**

```json
{
  "sender": "scammer@upi",
  "receiver": "victim@upi",
  "amount": 20000,
  "device": "Unknown",
  "timestamp": "2025-10-04T02:15:00"
}
```

**Response:**

```json
{
  "fraud": true,
  "method": "ml"
}
```

---

## 🧠 Machine Learning

* Trains a **Logistic Regression classifier** on UPI transaction data (`upi_transactions.csv`)
* Extracted features:

  * Amount
  * Device (encoded)
  * Transaction hour
* Model retrains **every N new transactions** for continuous learning
* Pickle files saved for reuse: `fraud_model.pkl`, `device_encoder.pkl`

Test ML prediction:

```bash
python test_ml_prediction.py
```

---

## 🛠️ Roadmap

* 🔄 Add real-time streaming with Kafka
* 📈 Build React-based admin dashboard
* 🧩 Extend ML with Deep Learning (LSTMs for time-series)
* ☁️ Deploy via Docker Compose + Kubernetes

---

✍️ **Author**: Alexander Aryan

---

👉 Do you want me to also generate a **fancy GitHub badge style README** (with shields.io badges for Python, Flask, MongoDB, etc.) so it looks professional on your repo front page?
