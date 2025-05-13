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
RANGE_WINDOW = 10  # candles used to define a range
BREAKOUT_THRESHOLD = 0.01  # 1% breakout range buffer

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

    range_df = df.iloc[-(RANGE_WINDOW+1):-1]
    latest = df.iloc[-1]

    range_high = range_df["high"].max()
    range_low = range_df["low"].min()

    breakout_up = latest["high"] > range_high * (1 + BREAKOUT_THRESHOLD)
    breakout_down = latest["low"] < range_low * (1 - BREAKOUT_THRESHOLD)

    if breakout_up and last_signal_sent != "up":
        message = f"🚀 *Breakout UP Detected!*\nPrice: {latest['close']:.2f}\nAbove Range: {range_high:.2f}"
        send_telegram_message(message)
        last_signal_sent = "up"
    elif breakout_down and last_signal_sent != "down":
        message = f"📉 *Breakout DOWN Detected!*\nPrice: {latest['close']:.2f}\nBelow Range: {range_low:.2f}"
        send_telegram_message(message)
        last_signal_sent = "down"
    elif not breakout_up and not breakout_down:
        last_signal_sent = None  # reset signal

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

            # If still within same candle
            if tick_time < last_open_time + GRANULARITY:
                last_candle["close"] = tick_price
                last_candle["high"] = max(last_candle["high"], tick_price)
                last_candle["low"] = min(last_candle["low"], tick_price)
            else:
                # New candle
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

                # Pattern check only on new candle close
                df = pd.DataFrame(candles)
                check_for_breakout(df)

@app.get("/", response_class=HTMLResponse)
async def get_chart_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Volatility 75 - Live Candlestick</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    </head>
    <body>
        <h2>Volatility 75 - 1 Minute Candlestick Chart</h2>
        <div id="chart" style="width: 100%; height: 600px;"></div>
        <script>
            async function loadCandles() {
                const res = await fetch('/candles');
                const data = await res.json();
                const c = data.candles;

                const trace = {
                    x: c.map(c => new Date(c.epoch * 1000)),
                    open: c.map(c => c.open),
                    high: c.map(c => c.high),
                    low: c.map(c => c.low),
                    close: c.map(c => c.close),
                    type: 'candlestick',
                    increasing: { line: { color: 'green' } },
                    decreasing: { line: { color: 'red' } }
                };

                Plotly.react('chart', [trace], {
                    title: 'Volatility 75 - Live 1m Chart',
                    xaxis: { title: 'Time' },
                    yaxis: { title: 'Price' }
                });
            }

            loadCandles();
            setInterval(loadCandles, 60000); // refresh every 60s
        </script>
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

