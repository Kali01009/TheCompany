import websocket
import json
import pandas as pd
import time
import threading
from main import send_telegram_message

# Constants
SYMBOL = "R_10"
INTERVAL = 60          # 1-minute candles
CANDLE_COUNT = 500     # Analyze past 500 candles
REFRESH_INTERVAL = 60  # Analyze every 60 seconds

# Global DataFrame to store candles
candle_df = pd.DataFrame()

# Pattern Detection Logic
def identify_patterns(df):
    patterns = set()

    for i in range(50, len(df) - 1):
        window = df.iloc[i-50:i]

        # Double Top
        if abs(window["high"].iloc[-1] - window["high"].iloc[-3]) < 0.05 and window["close"].iloc[-1] < window["open"].iloc[-1]:
            patterns.add("🔻 Double Top")

        # Double Bottom
        if abs(window["low"].iloc[-1] - window["low"].iloc[-3]) < 0.05 and window["close"].iloc[-1] > window["open"].iloc[-1]:
            patterns.add("🔺 Double Bottom")

        # Symmetrical Triangle
        recent_highs = window["high"].tail(20)
        recent_lows = window["low"].tail(20)
        if recent_highs.max() - recent_lows.min() < 0.2 * window["close"].mean():
            patterns.add("🔺 Symmetrical Triangle")

        # Bullish Flag
        if (window["close"].iloc[-1] > window["close"].iloc[-2] and
            window["close"].iloc[-10] < window["close"].iloc[-1] and
            (window["high"].max() - window["low"].min()) / window["low"].min() < 0.02):
            patterns.add("🚩 Bullish Flag")

        # Wedges
        if (window["high"].diff().mean() < 0 and window["low"].diff().mean() > 0):
            patterns.add("📉 Falling Wedge")
        elif (window["high"].diff().mean() > 0 and window["low"].diff().mean() < 0):
            patterns.add("📈 Rising Wedge")

    return patterns

def analyze_data():
    if len(candle_df) >= 100:
        patterns = identify_patterns(candle_df.copy())
        if patterns:
            for p in patterns:
                send_telegram_message(f"[V10 1m] Pattern Detected: {p}")
        else:
            print("No pattern found.")
    else:
        print("Waiting for more data...")

# WebSocket callbacks
def on_message(ws, message):
    global candle_df
    data = json.loads(message)
    if "candles" in data:
        candles = data["candles"]
        new_df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close"])
        new_df["timestamp"] = pd.to_datetime(new_df["timestamp"], unit="s")

        # Keep only the latest 500 unique candles
        candle_df = pd.concat([candle_df, new_df]).drop_duplicates("timestamp")
        candle_df = candle_df.sort_values("timestamp").tail(CANDLE_COUNT).reset_index(drop=True)

def on_open(ws):
    print("WebSocket opened")
    ws.send(json.dumps({
        "ticks_history": SYMBOL,
        "style": "candles",
        "granularity": INTERVAL,
        "count": 100,
        "subscribe": 1
    }))

def on_error(ws, error):
    print("WebSocket error:", error)

def on_close(ws, code, reason):
    print("WebSocket closed:", reason)

# Run analysis every 60 seconds
def periodic_analysis():
    while True:
        time.sleep(REFRESH_INTERVAL)
        analyze_data()

# Start everything
if __name__ == "__main__":
    socket_url = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    ws = websocket.WebSocketApp(socket_url,
                                 on_open=on_open,
                                 on_message=on_message,
                                 on_error=on_error,
                                 on_close=on_close)

    # Start background thread
    analysis_thread = threading.Thread(target=periodic_analysis)
    analysis_thread.daemon = True
    analysis_thread.start()

    # Run WebSocket
    ws.run_forever()
