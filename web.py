import websocket
import json
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)

# Deriv WebSocket URL
ws_url = "wss://ws.binaryws.com/websockets/v3?app_id=1089"  # Replace with your app_id if needed

def on_message(ws, message):
    try:
        data = json.loads(message)
        logging.info(f"Received message: {data}")
        
        # You can process the received data here
        if "ticks" in data:
            logging.info(f"Received ticks: {data['ticks']}")
    except Exception as e:
        logging.error(f"Error processing message: {e}")

def on_error(ws, error):
    logging.error(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    logging.info(f"WebSocket closed with code: {close_status_code}, message: {close_msg}")

def on_open(ws):
    logging.info("WebSocket connection established!")

    # Example: Send a subscription message to start receiving market data (ticks)
    subscribe_message = {
        "ticks": "R_10",  # Example symbol for volatility index (can be changed)
        "granularity": 60  # Granularity for the ticks (can be changed)
    }

    ws.send(json.dumps(subscribe_message))
    logging.info(f"Sent subscription message: {subscribe_message}")

def run_websocket():
    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    # Keep WebSocket connection alive
    while True:
        try:
            ws.run_forever()
        except Exception as e:
            logging.error(f"WebSocket encountered an error: {e}")
            time.sleep(5)  # Wait for 5 seconds before trying to reconnect
