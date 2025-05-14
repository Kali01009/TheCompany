import asyncio
import json
import websockets
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# WebSocket connection details
SYMBOL = "R_75"
GRANULARITY = 60
COUNT = 50
APP_ID = 1089
WS_URL = f"wss://ws.binaryws.com/websockets/v3?app_id={APP_ID}"

# Global candle data
candles = []

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
    return data.get("candles", [])

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

@app.get("/", response_class=HTMLResponse)
async def get_table_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live Candlestick Data - Table</title>
        <style>
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
            th { background-color: #eee; }
        </style>
    </head>
    <body>
        <h2>Volatility 75 - Live Candlestick Table</h2>
        <table id="candle-table">
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Open</th>
                    <th>High</th>
                    <th>Low</th>
                    <th>Close</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>

        <script>
            async function loadCandles() {
                const res = await fetch('/candles');
                const data = await res.json();
                const tbody = document.querySelector('#candle-table tbody');
                tbody.innerHTML = '';

                data.candles.slice().reverse().forEach(c => {
                    const row = document.createElement('tr');
                    const date = new Date(c.epoch * 1000).toLocaleTimeString();
                    row.innerHTML = `
                        <td>${date}</td>
                        <td>${c.open.toFixed(2)}</td>
                        <td>${c.high.toFixed(2)}</td>
                        <td>${c.low.toFixed(2)}</td>
                        <td>${c.close.toFixed(2)}</td>
                    `;
                    tbody.appendChild(row);
                });
            }

            loadCandles();
            setInterval(loadCandles, 60000); // update every 60 seconds
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
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
