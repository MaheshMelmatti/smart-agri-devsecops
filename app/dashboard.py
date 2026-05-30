from flask import Flask, render_template, jsonify
import pandas as pd
import boto3
import os

app = Flask(__name__)

BUCKET_NAME = os.environ.get("S3_BUCKET", "smart-agri-bucket1")
# Always resolve CSV path relative to this file, not the working directory
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "sensor_data.csv")

def fetch_csv_from_s3():
    try:
        s3 = boto3.client('s3')
        s3.download_file(BUCKET_NAME, "sensor_data.csv", FILE_PATH)
        print("S3 download OK -> " + FILE_PATH)
    except Exception as e:
        print(f"S3 download error: {e}")

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/metrics-data')
def metrics_data():
    try:
        fetch_csv_from_s3()

        df = pd.read_csv(FILE_PATH)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

        print("Columns found:", df.columns.tolist())
        print("Rows:", len(df))

        latest = df.iloc[-1]

        soil        = float(latest["soil_moisture"])
        temperature = float(latest["temperature"])
        humidity    = float(latest["humidity"])
        status      = "Irrigation Alert" if soil < 30 else "Normal"

        # Check if last reading is stale (older than 5 minutes)
        from datetime import datetime
        try:
            last_time    = datetime.strptime(str(latest["timestamp"]), "%Y-%m-%d %H:%M:%S")
            age_seconds  = abs((datetime.utcnow() - last_time).total_seconds())
            sensor_online = age_seconds < 300  # 5 minutes tolerance
        except:
            sensor_online = True

        return jsonify({
            "soil": soil, "temperature": temperature,
            "humidity": humidity, "status": status,
            "sensor_online": sensor_online
        })

    except Exception as e:
        print(f"metrics_data error: {e}")
        return jsonify({"soil": None, "temperature": None, "humidity": None, "status": "No Data", "sensor_online": False, "error": str(e)})

@app.route('/debug')
def debug():
    info = {
        "base_dir":       BASE_DIR,
        "file_path":      FILE_PATH,
        "file_exists":    os.path.exists(FILE_PATH),
        "bucket":         BUCKET_NAME,
        "cwd":            os.getcwd(),
    }
    if os.path.exists(FILE_PATH):
        df = pd.read_csv(FILE_PATH)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        info["columns"]   = df.columns.tolist()
        info["row_count"] = len(df)
        info["last_row"]  = df.iloc[-1].to_dict() if len(df) > 0 else {}
    return jsonify(info)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)