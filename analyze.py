import websocket
import json
import pandas as pd
import numpy as np
from main import send_telegram_message

# Constants
SYMBOL = "R_10"
INTERVAL = 60  # 1-minute candles
CANDLE_COUNT = 100

def identify_patterns(df):
    patterns = []

    # Simple breakout detection (for future enhancement)
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Detect double top / double bottom
    if abs(df["high"].iloc[-1] - df["high"].iloc[-3]) < 0.05 and last["close"] < last["open"]:
        patterns.append("🔻 Possible Double Top detected")
    elif abs(df["low"].iloc[-1] - df["low"].iloc[-3]) < 0.05 and last["close"] > last["open"]:
        patterns.append("🔺 Possible Double Bottom detected")

    # Detect triangle compression (symmetric)
    recent_highs = df["high"].tail(10)
    recent_lows = df["low"].tail(10)
    if recent_highs.max() - recent_lows.min() < 0.2 * df["close"].mean():
        patterns.append("🔺 Symmetrical Triangle forming")

    # Detect flag/pennant (basic version)
    if (last["close"] > prev["close"] and 
        df["close"].iloc[-5] < df["close"].iloc[-1] and
        (df["high"].max() - df["low"].min()) / df["low"].min() < 0.02):
        patterns.append("🚩 Possible Bullish Flag or Pennant")

    # Falling wedge / rising wedge estimate
    if (df["high"].diff().mean() < 0 and df["low"].diff().mean() > 0):
        patterns.append("🔻 Falling Wedge forming (bullish)")
    elif (df["high"].diff().mean() > 0 and df["low"].diff().mean() < 0):
        patterns.append("🔺 Rising Wedge forming (bearish)")

    return patterns

# WebSocket handlers
def on_message(ws, message):
    data = json.loads(message)
    if "candles" in data:
        candles = data["candles"]
        df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")

        patterns = identify_patterns(df)
        for p in patterns:
            send_telegram_message(f"[V10] {p}")

def on_open(ws):
    print("WebSocket opened")
    ws.send(json.dumps({
        "ticks_history": SYMBOL,
        "style": "candles",
        "granularity": INTERVAL,
        "count": CANDLE_COUNT,
        "subscribe": 1
    }))

def on_error(ws, error):
    print("WebSocket error:", error)

def on_close(ws, code, reason):
    print("WebSocket closed:", reason)

# Run pattern detection
if __name__ == "__main__":
    socket = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    ws = websocket.WebSocketApp(socket,
                                 on_open=on_open,
                                 on_message=on_message,
                                 on_error=on_error,
                                 on_close=on_close)
    ws.run_forever()
