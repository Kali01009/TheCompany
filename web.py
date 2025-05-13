import asyncio
import json
import time
import websockets
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# Store latest 50 candles in memory
candles = []

# Symbol and settings
SYMBOL = "R_75"  # Volatility 75 Index
GRANULARITY = 60  # 1-minute candles
COUNT = 50  # number of candles to keep
APP_ID = 1089  # Deriv app_id (you can change this if you have your own)

# WebSocket URL
WS_URL = f"wss://ws.binaryws.com/websockets/v3?app_id={APP_ID}"

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

async def candle_updater():
    global candles
    async with websockets.connect(WS_URL) as ws:
        # Get initial candles
        candles = await fetch_initial_candles(ws)

        # Subscribe to live ticks
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

            # If still within the same minute
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

# Run the WebSocket updater in background when FastAPI starts
@app.on_event("startup")
async def start_updater():
    asyncio.create_task(candle_updater())

# Run app
if __name__ == "__main__":
    uvicorn.run("web:app", host="0.0.0.0", port=8000)
