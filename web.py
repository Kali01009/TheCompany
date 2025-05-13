import os
import json
import logging
import threading
import time

import websocket
from flask import Flask, Response

# Setup logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Deriv WebSocket URL
ws_url = "wss://ws.binaryws.com/websockets/v3?app_id=1089"

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
        "ticks": "R_10"
    }
    ws.send(json.dumps(subscribe_message))
    logging.info(f"Sent subscription message: {subscribe_message}")

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
            time.sleep(5)

# Start WebSocket listener in background thread
threading.Thread(target=run_websocket, daemon=True).start()

@app.route('/')
def index():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <title>Deriv Tick Data Viewer</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          background: #f4f4f4;
          padding: 20px;
          color: #333;
        }
        h1 {
          color: #444;
        }
        #output {
          margin-top: 20px;
          padding: 10px;
          background: white;
          border: 1px solid #ddd;
          height: 400px;
          overflow-y: scroll;
        }
        .tick {
          margin-bottom: 10px;
          border-bottom: 1px solid #ccc;
          padding-bottom: 5px;
        }
      </style>
    </head>
    <body>

      <h1>Deriv Tick Data (R_10)</h1>
      <div id="output">Connecting to WebSocket...</div>

      <script>
        const output = document.getElementById('output');

        const socket = new WebSocket("wss://ws.binaryws.com/websockets/v3?app_id=1089");

        socket.onopen = function () {
          output.innerHTML += "<p><strong>WebSocket connection established.</strong></p>";
          const subscribeMsg = {
            "ticks": "R_10"
          };
          socket.send(JSON.stringify(subscribeMsg));
        };

        socket.onmessage = function (event) {
          const data = JSON.parse(event.data);
          const now = new Date().toLocaleTimeString();
          if (data.tick) {
            const tickInfo = `
              <div class="tick">
                <strong>Time:</strong> ${now}<br>
                <strong>Symbol:</strong> ${data.tick.symbol}<br>
                <strong>Price:</strong> ${data.tick.quote}<br>
                <strong>Epoch:</strong> ${data.tick.epoch}
              </div>
            `;
            output.innerHTML = tickInfo + output.innerHTML;
          } else {
            output.innerHTML += "<p>Received: " + JSON.stringify(data) + "</p>";
          }
        };

        socket.onerror = function (error) {
          output.innerHTML += "<p style='color:red;'>WebSocket error: " + error.message + "</p>";
        };

        socket.onclose = function () {
          output.innerHTML += "<p><strong>WebSocket connection closed.</strong></p>";
        };
      </script>

    </body>
    </html>
    """
    return Response(html_content, mimetype='text/html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Use Render's PORT variable
    app.run(host="0.0.0.0", port=port)
