from flask import Flask, render_template, jsonify
import pandas as pd
import boto3
import os

app = Flask(__name__)

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
BUCKET_NAME = os.environ.get("S3_BUCKET", "smart-agri-bucket1")
FILE_PATH   = os.path.join(BASE_DIR, "sensor_data.csv")

def fetch_csv_from_s3():
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id     = os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY"),
            region_name           = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        )
        s3.download_file(BUCKET_NAME, "sensor_data.csv", FILE_PATH)
        return True
    except Exception as e:
        print("S3 error: " + str(e))
        return False

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/metrics-data")
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
                        "humidity": humidity, "status": status, "sensor_online": s3_ok})
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
