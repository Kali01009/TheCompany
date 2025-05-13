import os
import json
import logging
import threading
import time

import websocket
from flask import Flask

# Setup logging
logging.basicConfig(level=logging.INFO)

# Flask app
app = Flask(__name__)

# Deriv WebSocket URL (Use your own app_id if needed)
ws_url = "wss://ws.binaryws.com/websockets/v3?app_id=1089"

# WebSocket event handlers
def on_message(ws, message):
    try:
        data = json.loads(message)
        logging.info(f"Received message: {data}")
        if "tick" in data:
            logging.info(f"Tick data: {data['tick']}")
    except Exception as e:
        logging.error(f"Error processing message: {e}")

def on_error(ws, error):
    logging.error(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    logging.info(f"WebSocket closed with code: {close_status_code}, message: {close_msg}")

def on_open(ws):
    logging.info("WebSocket connection established!")
    subscribe_message = {
        "ticks": "R_10"  # Subscribe to volatility index R_10
    }
    ws.send(json.dumps(subscribe_message))
    logging.info(f"Sent subscription message: {subscribe_message}")

# Run WebSocket client
def run_websocket():
    while True:
        try:
            ws = websocket.WebSocketApp(
                ws_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            ws.run_forever()
        except Exception as e:
            logging.error(f"WebSocket encountered an error: {e}")
            time.sleep(5)  # Wait before reconnecting

# Start WebSocket in a background thread
threading.Thread(target=run_websocket, daemon=True).start()

# Flask route for Render to detect a running server
@app.route('/')
def index():
    return "WebSocket client is running with Flask."

# Start Flask app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Render will set the PORT environment variable
    app.run(host="0.0.0.0", port=port)
