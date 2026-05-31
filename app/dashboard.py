from flask import Flask, render_template, jsonify, redirect, url_for, session, request, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import boto3
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "smart-agri-secret-2024")

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "users.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

BUCKET_NAME = os.environ.get("S3_BUCKET", "smart-agri-bucket1")
FILE_PATH   = os.path.join(BASE_DIR, "sensor_data.csv")

class User(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(100), nullable=False)
    email    = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

with app.app_context():
    db.create_all()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def fetch_csv_from_s3():
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id     = os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY"),
            region_name           = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        )
        s3.download_file(BUCKET_NAME, "sensor_data.csv", FILE_PATH)
        print("S3 download OK -> " + FILE_PATH)
        return True
    except Exception as e:
        print("S3 download error: " + str(e))
        return False

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return redirect(url_for("register"))
        user = User(name=name, email=email, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user     = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))
        session["user_id"]   = user.id
        session["user_name"] = user.name
        return redirect(url_for("home"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def home():
    return render_template("index.html", user_name=session.get("user_name"))

@app.route("/metrics-data")
@login_required
def metrics_data():
    try:
        s3_ok = fetch_csv_from_s3()
        if not s3_ok and not os.path.exists(FILE_PATH):
            return jsonify({"soil": None, "temperature": None, "humidity": None,
                            "status": "No Data", "sensor_online": False})
        df = pd.read_csv(FILE_PATH)
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        latest      = df.iloc[-1]
        soil        = float(latest["soil_moisture"])
        temperature = float(latest["temperature"])
        humidity    = float(latest["humidity"])
        status      = "Irrigation Alert" if soil < 30 else "Normal"
        return jsonify({"soil": soil, "temperature": temperature,
                        "humidity": humidity, "status": status, "sensor_online": True})
    except Exception as e:
        print("metrics_data error: " + str(e))
        return jsonify({"soil": None, "temperature": None, "humidity": None,
                        "status": "No Data", "sensor_online": False})

@app.route("/debug")
def debug():
    info = {"file_exists": os.path.exists(FILE_PATH), "bucket": BUCKET_NAME}
    if os.path.exists(FILE_PATH):
        df = pd.read_csv(FILE_PATH)
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        info["last_row"] = df.iloc[-1].to_dict() if len(df) > 0 else {}
    return jsonify(info)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
