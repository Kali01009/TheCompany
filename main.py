import asyncio
import json
import websockets
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import os

# === Candle Config ===
SYMBOL = "R_75"
GRANULARITY = 60  # 1-minute candles
COUNT = 20  # Last 20 candles (~20 minutes)
APP_ID = 1089
WS_URL = f"wss://ws.binaryws.com/websockets/v3?app_id={APP_ID}"

# Global candle list
candles = []

CSV_FILE = "candles.csv"

# === FastAPI App with Lifespan (replaces @on_event) ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(fetch_and_update_candles())
    yield

app = FastAPI(lifespan=lifespan)

# === Fetch Initial Candles from Deriv ===
async def fetch_initial_candles():
    async with websockets.connect(WS_URL) as ws:
        request = {
            "ticks_history": SYMBOL,
            "style": "candles",
            "granularity": GRANULARITY,
            "count": COUNT,
        }
        await ws.send(json.dumps(request))
        response = await ws.recv()
        data = json.loads(response)
        return data.get("candles", [])

# === Save new candles to CSV ===
def save_to_csv(new_candles):
    if not new_candles:
        return
    df = pd.DataFrame(new_candles)
    df["time"] = pd.to_datetime(df["epoch"], unit="s")
    df = df[["time", "open", "high", "low", "close"]]

    if not os.path.isfile(CSV_FILE):
        df.to_csv(CSV_FILE, index=False)
    else:
        # Avoid duplicate entries
        existing = pd.read_csv(CSV_FILE)
        existing_times = set(existing["time"])
        df = df[~df["time"].astype(str).isin(existing_times)]
        df.to_csv(CSV_FILE, mode='a', header=False, index=False)

# === Periodically Update Candles Every 60 Seconds ===
async def fetch_and_update_candles():
    global candles
    while True:
        try:
            new_data = await fetch_initial_candles()
            candles = new_data
            save_to_csv(new_data)
        except Exception as e:
            print("Error fetching or saving candles:", e)
        await asyncio.sleep(60)

# === Candles Data Endpoint ===
@app.get("/candles")
async def get_candles():
    return {"candles": candles}

# === HTML Display Page ===
@app.get("/", response_class=HTMLResponse)
async def display_table():
    if not candles:
        return "<h2>Loading data...</h2>"

    df = pd.DataFrame(candles)
    df["time"] = pd.to_datetime(df["epoch"], unit="s")
    df = df[["time", "open", "high", "low", "close"]]

    html_table = df.to_html(index=False)

    return f"""
    <html>
        <head>
            <title>R_75 - Last 20 Candles</title>
            <meta http-equiv="refresh" content="60">
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h2>R_75 - Last 20 One-Minute Candles</h2>
            {html_table}
            <p>Auto-refreshes every 60 seconds. Data also saved to <code>candles.csv</code>.</p>
        </body>
    </html>
    """

# === Run Locally ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
