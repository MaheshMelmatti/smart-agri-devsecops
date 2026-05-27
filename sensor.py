import random
import time
import csv
import boto3
from datetime import datetime

# ==============================
# AWS S3 CONFIGURATION
# ==============================

BUCKET_NAME = "smart-agri-bucket1"
FILE_NAME = "sensor_data.csv"

# Create AWS S3 client
s3 = boto3.client('s3')

# ==============================
# CREATE CSV FILE WITH HEADERS
# ==============================

with open(FILE_NAME, mode='w', newline='') as file:
    writer = csv.writer(file)

    writer.writerow([
        "Timestamp",
        "SoilMoisture",
        "Temperature",
        "Humidity",
        "Status"
    ])

print("====================================")
print(" Smart Agriculture Monitoring Started")
print(" Real-Time Sensor Simulation Running")
print("====================================\n")

# ==============================
# REAL-TIME SENSOR SIMULATION
# ==============================

while True:

    # Generate random sensor values
    moisture = random.randint(20, 90)
    temperature = random.randint(25, 40)
    humidity = random.randint(40, 80)

    # Current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Irrigation alert logic
    status = "Normal"

    if moisture < 30:
        status = "Irrigation Alert Triggered"

    # ==============================
    # DISPLAY LIVE DATA
    # ==============================

    print("====================================")
    print(f"Timestamp       : {timestamp}")
    print(f"Soil Moisture   : {moisture}")
    print(f"Temperature     : {temperature}")
    print(f"Humidity        : {humidity}")
    print(f"System Status   : {status}")
    print("====================================")

    # ==============================
    # SAVE DATA TO CSV
    # ==============================

    with open(FILE_NAME, mode='a', newline='') as file:

        writer = csv.writer(file)

        writer.writerow([
            timestamp,
            moisture,
            temperature,
            humidity,
            status
        ])

    # ==============================
    # UPLOAD CSV TO AWS S3
    # ==============================

    try:

        s3.upload_file(
            FILE_NAME,
            BUCKET_NAME,
            FILE_NAME
        )

        print(" Uploaded to AWS S3 Successfully\n")

    except Exception as e:

        print(" S3 Upload Error:", e)

    # ==============================
    # REAL-TIME DELAY
    # ==============================

    time.sleep(2)