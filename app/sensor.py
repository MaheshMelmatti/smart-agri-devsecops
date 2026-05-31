import random
import time
import csv
import boto3
from datetime import datetime
from prometheus_client import start_http_server, Gauge

# =========================
# AWS S3 Configuration
# =========================
BUCKET_NAME = "smart-agri-bucket1"
FILE_NAME = "sensor_data.csv"

s3 = boto3.client('s3')

# =========================
# Prometheus Metrics
# =========================
soil_metric = Gauge('soil_moisture', 'Soil Moisture Level')
temp_metric = Gauge('temperature', 'Temperature')
humidity_metric = Gauge('humidity', 'Humidity')

# Start Prometheus metrics server
start_http_server(8000)

print("Smart Agriculture Monitoring Started...")
print("Prometheus metrics running on port 8000")

# =========================
# CSV Header
# =========================
with open(FILE_NAME, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow([
        "Timestamp",
        "Soil Moisture",
        "Temperature",
        "Humidity",
        "Status"
    ])

# =========================
# Real-Time Monitoring Loop
# =========================
while True:

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    soil_moisture = random.randint(10, 90)
    temperature = random.randint(20, 40)
    humidity = random.randint(30, 80)

    # Irrigation Alert Logic
    if soil_moisture < 30:
        alert = "Irrigation Alert Triggered"
    else:
        alert = "Normal"

    # =========================
    # Update Prometheus Metrics
    # =========================
    soil_metric.set(soil_moisture)
    temp_metric.set(temperature)
    humidity_metric.set(humidity)

    # =========================
    # Print Data
    # =========================
    print("\nTimestamp:", timestamp)
    print("Soil Moisture:", soil_moisture)
    print("Temperature:", temperature)
    print("Humidity:", humidity)
    print("Status:", alert)

    # =========================
    # Save to CSV
    # =========================
    with open(FILE_NAME, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            timestamp,
            soil_moisture,
            temperature,
            humidity,
            alert
        ])

    # =========================
    # Upload to AWS S3
    # =========================
    try:
        # Read full file content first, then upload to avoid IncompleteBody
        with open(FILE_NAME, 'rb') as f:
            file_content = f.read()
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=FILE_NAME,
            Body=file_content,
            ContentLength=len(file_content)
        )
        print("Uploaded to S3 successfully")
    except Exception as e:
        print("S3 Upload Error:", e)

    # Wait 5 seconds
    time.sleep(10)