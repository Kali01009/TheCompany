import websocket
import json
import logging
import time

logging.basicConfig(level=logging.INFO)
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
    logging.info(f"WebSocket closed: {close_status_code} - {close_msg}")


def on_open(ws):
    logging.info("WebSocket connected.")

    # Subscribe to tick data for R_10
    subscribe_msg = {"ticks": "R_10"}
    ws.send(json.dumps(subscribe_msg))
    logging.info(f"Sent subscription: {subscribe_msg}")


def run_websocket():
    ws = websocket.WebSocketApp(ws_url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    while True:
        try:
            ws.run_forever()
        except Exception as e:
            logging.error(f"WebSocket error: {e}")
            time.sleep(5)
