import asyncio
import json
import time
import websockets
import pandas as pd
import requests
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# === Telegram Bot Configuration ===
BOT_TOKEN = "7819951392:AAFkYd9-sblexjXNqgIfhbWAIC1Lr6NmPpo"
CHAT_ID = "6734231237"

def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Failed to send Telegram message:", e)

# === Candlestick Data Store ===
candles = []
SYMBOL = "R_75"
GRANULARITY = 60
COUNT = 50
APP_ID = 1089
WS_URL = f"wss://ws.binaryws.com/websockets/v3?app_id={APP_ID}"

# === Pattern Detection Settings ===
RANGE_WINDOW = 10
BREAKOUT_THRESHOLD = 0.01
last_signal_sent = None

async def fetch_initial_candles(ws):
    request = {
        "ticks_history": SYMBOL,
        "style": "candles",
        "granularity": GRANULARITY,
        "count": COUNT
    }
    await ws.send(json.dumps(request))
    response = await ws.recv()
    data = json.loads(response)
    if "candles" in data:
        return data["candles"]
    return []

def check_for_breakout(df: pd.DataFrame):
    global last_signal_sent
    if len(df) < RANGE_WINDOW + 1:
        return

    range_df = df.iloc[-(RANGE_WINDOW + 1):-1]
    latest = df.iloc[-1]

    range_high = range_df["high"].max()
    range_low = range_df["low"].min()

    breakout_up = latest["high"] > range_high * (1 + BREAKOUT_THRESHOLD)
    breakout_down = latest["low"] < range_low * (1 - BREAKOUT_THRESHOLD)

    if breakout_up and last_signal_sent != "up":
        message = f"🚀 Breakout UP Detected!\nPrice: {latest['close']:.2f}\nAbove Range: {range_high:.2f}"
        send_telegram_message(message)
        last_signal_sent = "up"
    elif breakout_down and last_signal_sent != "down":
        message = f"📉 Breakout DOWN Detected!\nPrice: {latest['close']:.2f}\nBelow Range: {range_low:.2f}"
        send_telegram_message(message)
        last_signal_sent = "down"
    elif not breakout_up and not breakout_down:
        last_signal_sent = None

async def candle_updater():
    global candles
    async with websockets.connect(WS_URL) as ws:
        candles = await fetch_initial_candles(ws)

        tick_request = {
            "ticks": SYMBOL,
            "subscribe": 1
        }
        await ws.send(json.dumps(tick_request))

        async for message in ws:
            tick_data = json.loads(message)
            if "tick" not in tick_data:
                continue

            tick = tick_data["tick"]
            tick_time = tick["epoch"]
            tick_price = float(tick["quote"])

            if not candles:
                continue

            last_candle = candles[-1]
            last_open_time = last_candle["epoch"]

            if tick_time < last_open_time + GRANULARITY:
                last_candle["close"] = tick_price
                last_candle["high"] = max(last_candle["high"], tick_price)
                last_candle["low"] = min(last_candle["low"], tick_price)
            else:
                new_candle = {
                    "epoch": last_open_time + GRANULARITY,
                    "open": tick_price,
                    "high": tick_price,
                    "low": tick_price,
                    "close": tick_price
                }
                candles.append(new_candle)
                if len(candles) > COUNT:
                    candles.pop(0)

                df = pd.DataFrame(candles)
                check_for_breakout(df)

@app.get("/", response_class=HTMLResponse)
async def get_table_page():
    table_rows = ""
    for candle in reversed(candles):
        row = f"""
        <tr>
            <td>{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(candle['epoch']))}</td>
            <td>{candle['open']:.2f}</td>
            <td>{candle['high']:.2f}</td>
            <td>{candle['low']:.2f}</td>
            <td>{candle['close']:.2f}</td>
        </tr>
        """
        table_rows += row

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Volatility 75 - Candlestick Table</title>
        <meta http-equiv="refresh" content="60">
        <style>
            body {{
                font-family: Arial, sans-serif;
                padding: 20px;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
            }}
            th, td {{
                border: 1px solid #ddd;
                text-align: center;
                padding: 8px;
            }}
            th {{
                background-color: #f2f2f2;
            }}
        </style>
    </head>
    <body>
        <h2>Volatility 75 - Candlestick Data (Last {len(candles)} Entries)</h2>
        <p>Auto-refreshes every 60 seconds</p>
        <table>
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Open</th>
                    <th>High</th>
                    <th>Low</th>
                    <th>Close</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </body>
    </html>
    """

@app.get("/candles")
async def get_candle_data():
    return {"candles": candles}

@app.on_event("startup")
async def start_updater():
    asyncio.create_task(candle_updater())

if __name__ == "__main__":
    uvicorn.run("web:app", host="0.0.0.0", port=8000)
