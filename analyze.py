import websocket
import json
import pandas as pd
import threading
import time
import requests

BOT_TOKEN = "7819951392:AAFkYd9-sblexjXNqgIfhbWAIC1Lr6NmPpo"
CHAT_ID = "6734231237"

index_candles = {}
subscribed_indexes = []

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram Error:", e)

def detect_patterns(df):
    detected = []
    if len(df) < 20: return detected
    last = df.iloc[-1]
    recent_high = df['high'][-10:].max()
    recent_low = df['low'][-10:].min()
    if last['high'] > recent_high * 0.99:
        entry = last['close']
        sl = recent_low
        tp = entry + (entry - sl) * 1.5
        detected.append(("🚩 Bullish Flag", entry, sl, tp))
    return detected

def analyze_data_for_index(index):
    candles = index_candles.get(index, [])
    if len(candles) < 20:
        return

    df = pd.DataFrame(candles[-500:], columns=["timestamp", "open", "high", "low", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    detected = detect_patterns(df)

    for name, entry, sl, tp in detected:
        last_close = df["close"].iloc[-1]
        break_even = entry
        if sl * 0.99 < last_close < sl * 1.01:
            advice = "⚠️ Risky – Consider Exit"
        elif last_close > tp * 0.97:
            advice = "✅ Approaching TP – Watch"
        else:
            advice = "⏳ Hold"
        message = (
            f"📈 *{name}* detected on *{index}*\n"
            f"💰 Entry: `{entry:.2f}`\n"
            f"🛑 Stop Loss: `{sl:.2f}`\n"
            f"🎯 Take Profit: `{tp:.2f}`\n"
            f"🔁 Break Even: `{break_even:.2f}`\n"
            f"{advice}"
        )
        send_telegram_message(message)

def on_message_factory(index):
    def on_message(ws, message):
        data = json.loads(message)
        candles = []
        if "candles" in data:
            candles = data["candles"]
        elif "history" in data:
            candles = data["history"]["candles"]

        index_candles[index] = [
            [c["epoch"], c["open"], c["high"], c["low"], c["close"]]
            for c in candles
        ]
        analyze_data_for_index(index)
    return on_message

def run_websocket(index):
    ws = websocket.WebSocketApp(
        "wss://ws.binaryws.com/websockets/v3?app_id=1089",
        on_open=lambda ws: ws.send(json.dumps({
            "ticks_history": index,
            "style": "candles",
            "granularity": 60,
            "count": 500,
            "subscribe": 1
        })),
        on_message=on_message_factory(index),
        on_error=lambda ws, error: print(f"{index} WebSocket error:", error),
        on_close=lambda ws, code, msg: print(f"{index} WebSocket closed")
    )
    ws.run_forever()

def start_analysis(indexes):
    global subscribed_indexes
    subscribed_indexes = indexes
    for index in indexes:
        threading.Thread(target=run_websocket, args=(index,)).start()
