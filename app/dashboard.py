from flask import Flask, render_template, jsonify
import pandas as pd
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/metrics-data')
def metrics_data():

    try:

        df = pd.read_csv("sensor_data.csv")

        latest = df.iloc[-1]

        soil = float(latest["soil_moisture"])
        temperature = float(latest["temperature"])
        humidity = float(latest["humidity"])

        if soil < 30:
            status = "Irrigation Alert"
        else:
            status = "Normal"

        return jsonify({
            "soil": soil,
            "temperature": temperature,
            "humidity": humidity,
            "status": status
        })

    except Exception as e:

        return jsonify({
            "soil": 0,
            "temperature": 0,
            "humidity": 0,
            "status": "No Data"
        })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)