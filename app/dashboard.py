from flask import Flask, render_template, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
import pandas as pd
import boto3
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "smart-agri-secret-2024")

# ── Database ──────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "users.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ── Config ────────────────────────────────────────────────────
BUCKET_NAME = os.environ.get("S3_BUCKET", "smart-agri-bucket1")
FILE_PATH   = os.path.join(BASE_DIR, "sensor_data.csv")
GMAIL_USER  = os.environ.get("GMAIL_USER", "")
GMAIL_PASS  = os.environ.get("GMAIL_PASS", "")

# ── Alert state ───────────────────────────────────────────────
last_alert_sent = {"irrigation": None, "offline": None}

# ── Google OAuth ──────────────────────────────────────────────
oauth  = OAuth(app)
google = oauth.register(
    name="google",
    client_id           = os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret       = os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs       = {"scope": "openid email profile"}
)

# ── Model ─────────────────────────────────────────────────────
class User(db.Model):
    id    = db.Column(db.Integer, primary_key=True)
    name  = db.Column(db.String(100))
    email = db.Column(db.String(150), unique=True, nullable=False)

with app.app_context():
    db.create_all()

# ── Auth decorator ────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_email" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ── Email ─────────────────────────────────────────────────────
def send_email(to_email, subject, body_html):
    if not GMAIL_USER or not GMAIL_PASS:
        print("Email not configured")
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = GMAIL_USER
        msg["To"]      = to_email
        msg.attach(MIMEText(body_html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_PASS)
            s.sendmail(GMAIL_USER, to_email, msg.as_string())
        print("Email sent to " + to_email)
    except Exception as e:
        print("Email error: " + str(e))

def notify_all(subject, body_html):
    for user in User.query.all():
        send_email(user.email, subject, body_html)

def irrigation_email(soil):
    return f"""
    <div style="font-family:Inter,sans-serif;background:#030712;padding:32px;border-radius:16px;max-width:520px;margin:auto">
      <div style="text-align:center;margin-bottom:24px">
        <div style="font-size:48px">&#128680;</div>
        <h2 style="color:#f87171;margin:12px 0 4px;font-size:22px">Irrigation Alert</h2>
        <p style="color:#64748b;font-size:13px">Smart Agriculture Monitoring System</p>
      </div>
      <div style="background:rgba(248,113,113,0.08);border:1px solid rgba(248,113,113,0.2);border-radius:12px;padding:20px;margin-bottom:20px">
        <p style="color:#f1f5f9;font-size:15px;margin:0">Soil moisture dropped to <strong style="color:#f87171">{soil}%</strong> — below critical threshold of 30%.</p>
        <p style="color:#94a3b8;font-size:13px;margin:10px 0 0">Please activate irrigation immediately to prevent crop damage.</p>
      </div>
      <div style="text-align:center;color:#475569;font-size:12px">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Smart Agriculture</div>
    </div>"""

def offline_email():
    return f"""
    <div style="font-family:Inter,sans-serif;background:#030712;padding:32px;border-radius:16px;max-width:520px;margin:auto">
      <div style="text-align:center;margin-bottom:24px">
        <div style="font-size:48px">&#128225;</div>
        <h2 style="color:#fb923c;margin:12px 0 4px;font-size:22px">Sensor Offline</h2>
        <p style="color:#64748b;font-size:13px">Smart Agriculture Monitoring System</p>
      </div>
      <div style="background:rgba(251,146,60,0.08);border:1px solid rgba(251,146,60,0.2);border-radius:12px;padding:20px;margin-bottom:20px">
        <p style="color:#f1f5f9;font-size:15px;margin:0">No data received from the field sensor.</p>
        <p style="color:#94a3b8;font-size:13px;margin:10px 0 0">Please ensure sensor.py is running to resume live monitoring.</p>
      </div>
      <div style="text-align:center;color:#475569;font-size:12px">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Smart Agriculture</div>
    </div>"""

# ── S3 ────────────────────────────────────────────────────────
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

# ── Auth routes ───────────────────────────────────────────────
@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/login/google")
def login_google():
    redirect_uri = url_for("auth_callback", _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/auth/callback")
def auth_callback():
    token     = google.authorize_access_token()
    user_info = token.get("userinfo")
    if not user_info:
        return redirect(url_for("login"))

    email = user_info["email"]
    name  = user_info.get("name", email.split("@")[0])

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(name=name, email=email)
        db.session.add(user)
        db.session.commit()

    session["user_email"] = email
    session["user_name"]  = name
    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── Dashboard ─────────────────────────────────────────────────
@app.route("/")
@login_required
def home():
    return render_template("index.html", user_name=session.get("user_name"))

@app.route("/metrics-data")
@login_required
def metrics_data():
    global last_alert_sent
    try:
        s3_ok = fetch_csv_from_s3()

        if not s3_ok and not os.path.exists(FILE_PATH):
            if last_alert_sent["offline"] is None:
                last_alert_sent["offline"] = datetime.now()
                notify_all("Sensor Offline - Smart Agriculture", offline_email())
            return jsonify({"soil": None, "temperature": None, "humidity": None,
                            "status": "No Data", "sensor_online": False})

        last_alert_sent["offline"] = None

        df = pd.read_csv(FILE_PATH)
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        latest      = df.iloc[-1]
        soil        = float(latest["soil_moisture"])
        temperature = float(latest["temperature"])
        humidity    = float(latest["humidity"])
        status      = "Irrigation Alert" if soil < 30 else "Normal"

        if soil < 30:
            if last_alert_sent["irrigation"] is None:
                last_alert_sent["irrigation"] = datetime.now()
                notify_all("Irrigation Alert - Smart Agriculture", irrigation_email(soil))
        else:
            last_alert_sent["irrigation"] = None

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
