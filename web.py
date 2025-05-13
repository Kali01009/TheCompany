from flask import Flask, render_template_string, jsonify
import json
import os
import time
from threading import Thread
from main import send_telegram_message, get_signals
import pandas as pd
import plotly.express as px

app = Flask(__name__)

# Store signals in memory (global variable)
signals = []

# Chart template for closing prices
chart_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Signal Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; padding: 40px; background: #f4f4f4; }
        h1 { color: #333; }
        ul { list-style: none; padding: 0; }
        li { background: #fff; margin: 10px 0; padding: 10px; border-left: 5px solid #6a1b9a; }
        button {
            padding: 10px 20px;
            background-color: #6a1b9a;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background-color: #9c4d9d;
        }
        .container {
            width: 80%;
            margin: 0 auto;
        }
        #chart-container {
            width: 100%;
            height: 400px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Live Signals</h1>
        <ul>
            {% for signal in signals %}
                <li>{{ signal }}</li>
            {% endfor %}
        </ul>
        
        <button onclick="sendHello()">Send Hello to Telegram</button>

        <h2>Live Closing Prices Chart</h2>
        <div id="chart-container">
            <canvas id="priceChart"></canvas>
        </div>

        <script>
            function sendHello() {
                fetch('/send_hello', {
                    method: 'GET',
                })
                .then(response => response.text())
                .then(data => alert(data))
                .catch(error => alert('Error sending message: ' + error));
            }

            // Draw chart
            const closingPrices = {{ closing_prices }};
            const ctx = document.getElementById('priceChart').getContext('2d');
            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: closingPrices.map((_, index) => index + 1), // x-axis labels
                    datasets: [{
                        label: 'Closing Prices',
                        data: closingPrices,
                        borderColor: '#6a1b9a',
                        fill: false,
                    }]
                },
                options: {
                    scales: {
                        x: { 
                            title: { display: true, text: 'Time (minutes)' }
                        },
                        y: {
                            title: { display: true, text: 'Price (USD)' }
                        }
                    }
                }
            });
        </script>
    </div>
</body>
</html>
"""

# Function to fetch signals from analyze.py (replaced with actual signal generation logic)
def fetch_live_signals():
    global signals
    while True:
        new_signals = get_signals()  # Get new signals from analyze.py
        if new_signals:
            signals = new_signals
        time.sleep(60)  # Update every 60 seconds

# Starting the signal-fetching thread
signal_thread = Thread(target=fetch_live_signals, daemon=True)
signal_thread.start()

@app.route('/')
def home():
    try:
        signals = get_signals()  # Try to fetch signals
    except Exception as e:
        signals = []  # If there's an error, fallback to an empty list
        print("Error fetching signals:", e)
    
    return render_template_string(HTML_TEMPLATE, signals=signals)

@app.route('/send_hello', methods=['GET'])
def send_hello():
    try:
        send_telegram_message("Hello")  # Sends a "Hello" message to Telegram
        return "Message sent to Telegram!"
    except Exception as e:
        return f"Error: {str(e)}", 500  # Return error message if something goes wrong

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
