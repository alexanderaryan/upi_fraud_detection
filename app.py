from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymongo import MongoClient
import pandas as pd
from bson.json_util import dumps
from bson.regex import Regex
from datetime import datetime
import os
from functools import wraps

from flask_bcrypt import Bcrypt
from block_sender_db import is_sender_blocked, block_sender
from retrain_model import retrain_model
from ml_predictor import predict_fraud_ml


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


# Simple blacklist
BLACKLIST = {"scam@upi", "fraud123@okaxis", "spam@okhdfc"}

# Counter for periodic retraining
NEW_FLAGGED_COUNTER = 0
N_RETRAIN = 500  # retrain after every 500 flagged transactions


app = Flask(__name__)
app.secret_key = "upi_fraud_detection"  # Replace with a strong secret in production!
bcrypt = Bcrypt(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function



# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["upi_fraud_db"]
transactions_collection = db["transactions"]
flagged = db["flagged_transactions"]

limiter = Limiter(get_remote_address, app=app)

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get("username"):
                return redirect(url_for("login", next=request.path))
            user = db["users"].find_one({"username": session["username"]})
            if not user or user.get("role") != required_role:
                return redirect(url_for("test_fraud_check"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Check if user already exists
        if db["users"].find_one({"username": username}):
            flash("⚠️ Username already exists. Please choose another.", "error")
            return render_template("signup.html")  # Stay on signup page

        # Decide role: first user = admin, others = user
        if db["users"].count_documents({}) == 0:
            role = "admin"
        else:
            role = "user"

        # Hash password
        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

        # Insert into DB
        db["users"].insert_one({
            "username": username,
            "password": hashed_pw,
            "role": role
        })

        flash("✅ Account created! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    next_url = request.args.get("next") or url_for("index")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = db["users"].find_one({"username": username})

        if user and bcrypt.check_password_hash(user["password"], password):
            # ✅ store login state
            session["logged_in"] = True
            session["username"] = username
            session["role"] = user.get("role", "user")
            return redirect(next_url)
        else:
            return render_template("login.html", error="Invalid credentials", next=next_url)

    return render_template("login.html", next=next_url)


@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))



def prepare_chart_data(df):
    # Convert 'time' to datetime
    df['time'] = pd.to_datetime(df['time'], errors='coerce')

    # Fraud by Day
    day_counts = df['time'].dt.date.value_counts().sort_index()
    day_labels = [str(d) for d in day_counts.index]
    day_data = day_counts.values.tolist()

    # Fraud by Hour
    hour_counts = df['time'].dt.hour.value_counts().sort_index()
    hour_labels = [str(h) for h in hour_counts.index]
    hour_data = hour_counts.values.tolist()

    # Fraud by Device
    device_counts = df['device'].value_counts()
    device_labels = device_counts.index.tolist()
    device_data = device_counts.values.tolist()

    return {
        'day_labels': day_labels,
        'day_data': day_data,
        'hour_labels': hour_labels,
        'hour_data': hour_data,
        'device_labels': device_labels,
        'device_data': device_data
    }

@app.route("/", methods=["GET", "POST"])
@role_required("admin")
def index():
    query_upi = request.form.get("upi_id") or request.args.get("upi_id")
    page = int(request.args.get("page", 1))
    per_page = 25
    skip = (page - 1) * per_page

    query = {}
    if query_upi:

        if query_upi:
            query["$or"] = [
                {"sender": {"$regex": query_upi, "$options": "i"}},
                {"receiver": {"$regex": query_upi, "$options": "i"}}
            ]

    total = flagged.count_documents(query)
    results = list(flagged.find(query).skip(skip).limit(per_page))
    df = pd.DataFrame(results)
    charts = prepare_chart_data(df) if not df.empty else {}


    return render_template("index.html", transactions=results, charts=charts, query_upi=query_upi,
                           page=page, total=total, per_page=per_page)


@app.route('/api/check_fraud', methods=['POST'])
@limiter.limit("10/minute")
def check_fraud():
    global NEW_FLAGGED_COUNTER

    data = request.get_json()

    # Extract transaction fields
    sender = data.get("sender", "").lower()
    receiver = data.get("receiver", "").lower()
    amount = float(data.get("amount", 0))
    device = data.get("device", "Unknown")
    timestamp = data.get("timestamp", datetime.utcnow().isoformat())

    try:
        dt = datetime.fromisoformat(timestamp)
    except:
        return jsonify({"error": "Invalid timestamp format"}), 400

    hour = dt.hour
    reasons = []

    # ------------------------
    # ML prediction
    # ------------------------
    try:
        ml_fraud = predict_fraud_ml(data)
        if ml_fraud:
            reasons.append("Detected as fraud by ML model")
    except Exception as e:
        logger.error("⚠️ ML prediction failed:", e)

    # ------------------------
    # Rule-based checks
    # ------------------------
    BLACKLIST = {"scam@upi", "fraud123@okaxis", "spam@okhdfc"}

    if sender in BLACKLIST or receiver in BLACKLIST:
        reasons.append("Blacklisted UPI ID")

    if is_sender_blocked(sender):
        reasons.append(f"Sender {sender} already blocked")

    if amount > 10000:
        reasons.append("High transaction amount")

    if hour < 5:
        reasons.append("Transaction during suspicious hours")

    allowed_devices = ["Android", "iOS", "Windows", "Linux"]
    if device not in allowed_devices:
        reasons.append("Unknown device")


    is_fraud = len(reasons) > 0

    # ------------------------
    # Log flagged transaction
    # ------------------------
    data["checked_at"] = datetime.datetime.now(datetime.UTC)
    data["is_fraud"] = is_fraud
    data["fraud_reasons"] = reasons
    flagged.insert_one(data)

    # ------------------------
    # Auto-block sender if fraud
    # ------------------------
    if is_fraud and not is_sender_blocked(sender):
        reason_str = "; ".join(reasons)
        block_sender(sender, reason=reason_str)
        logger.info(f"🚫 Sender {sender} blocked for reasons: {reason_str}")

    # ------------------------
    # Increment counter & retrain ML model after # of transactions
    # ------------------------
    if is_fraud:
        NEW_FLAGGED_COUNTER += 1

    if NEW_FLAGGED_COUNTER >= N_RETRAIN:
        logger.info(f"🔄 Retraining ML model after {NEW_FLAGGED_COUNTER} flagged transactions...")
        try:
            retrain_model()
        except Exception as e:
            logger.error("⚠️ Retraining failed:", e)
        NEW_FLAGGED_COUNTER = 0  # reset counter

    # ------------------------
    # Response
    # ------------------------
    return jsonify({
        "is_fraud": is_fraud,
        "reasons": reasons if reasons else ["Legit transaction"]
    })


@app.route("/test-fraud-check")
@login_required
def test_fraud_check():
    return render_template("test_form.html")


@app.route("/all-transactions")
@login_required
def all_transactions():
    page = int(request.args.get("page", 1))
    per_page = 20
    total = transactions_collection.count_documents({})

    txns = (
        transactions_collection
        .find({})
        .sort("time", -1)
        .skip((page - 1) * per_page)
        .limit(per_page)
    )

    return render_template(
        "all_transactions.html",
        transactions=txns,
        page=page,
        per_page=per_page,
        total=total,
        role=session.get("role")   # 👈 pass role explicitly
    )


@app.context_processor
def inject_user():
    return dict(session=session)


if __name__ == "__main__":
    logger.info("🚀 Starting UPI Fraud Detection Flask app...")
    app.run(debug=False)
