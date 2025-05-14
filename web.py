import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import pandas as pd
import plotly.graph_objects as go
import json

from analyze import index_candles  # Make sure this path is correct

app = FastAPI()

# Root endpoint (for testing)
@app.get("/", response_class=HTMLResponse)
def read_root():
    return HTMLResponse(content="<h1>Welcome to the Volatility Analyzer</h1>", status_code=200)

@app.get("/chart/{index}", response_class=HTMLResponse)
def candlestick_chart(index: str):
    # Check if the index data exists
    if index not in index_candles or len(index_candles[index]) < 20:
        return HTMLResponse(content="<h3>No data available for this index yet.</h3>", status_code=200)

    # Convert the candle data to a DataFrame
    df = pd.DataFrame(index_candles[index], columns=["timestamp", "open", "high", "low", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")

    # Create a candlestick chart using Plotly
    fig = go.Figure(data=[
        go.Candlestick(
            x=df["timestamp"],  # Timestamp on X-axis
            open=df["open"],     # Open price
            high=df["high"],     # High price
            low=df["low"],       # Low price
            close=df["close"],   # Close price
            increasing_line_color="green",  # Green for upward prices
            decreasing_line_color="red"    # Red for downward prices
        )
    ])

    # Customize chart layout
    fig.update_layout(
        title=f"{index} - Candlestick Chart",  # Chart title
        xaxis_title="Time",  # X-axis label
        yaxis_title="Price",  # Y-axis label
        xaxis_rangeslider_visible=False,  # Hide the range slider
        template="plotly_dark"  # Dark theme for the chart
    )

    # Generate HTML for the candlestick chart
    chart_html = fig.to_html(full_html=False)

    # Full HTML response including the chart
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{index} - Candlestick Chart</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #1e1e1e;
                color: white;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }}
            h1 {{
                font-size: 2em;
                text-align: center;
            }}
            .chart-container {{
                width: 80%;
                height: 80%;
                padding: 20px;
                background-color: #2c2f38;
                border-radius: 10px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            table, th, td {{
                border: 1px solid white;
                padding: 8px;
                text-align: center;
            }}
            th {{
                background-color: #444;
            }}
            tr:nth-child(even) {{
                background-color: #333;
            }}
        </style>
    </head>
    <body>
        <div class="chart-container">
            <h1>{index} - Candlestick Chart</h1>
            {chart_html}
            <h2>Live Data</h2>
            <table id="data-table">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Open</th>
                        <th>High</th>
                        <th>Low</th>
                        <th>Close</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Table rows will be inserted here by JavaScript -->
                </tbody>
            </table>
        </div>

        <script>
            const ws = new WebSocket('ws://localhost:8000/ws/{index}');  // Update WebSocket endpoint with the index
            const table = document.getElementById('data-table').getElementsByTagName('tbody')[0];

            ws.onmessage = function(event) {{
                const data = JSON.parse(event.data);
                const row = table.insertRow(0);
                row.insertCell(0).innerHTML = new Date(data.timestamp * 1000).toLocaleString();
                row.insertCell(1).innerHTML = data.open;
                row.insertCell(2).innerHTML = data.high;
                row.insertCell(3).innerHTML = data.low;
                row.insertCell(4).innerHTML = data.close;
            }};
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

# WebSocket endpoint to send live data updates
@app.websocket("/ws/{index}")
async def websocket_endpoint(websocket: WebSocket, index: str):
    await websocket.accept()
    try:
        while True:
            if index in index_candles and len(index_candles[index]) > 0:
                last_candle = index_candles[index][-1]
                candle_data = {
                    "timestamp": last_candle[0],
                    "open": last_candle[1],
                    "high": last_candle[2],
                    "low": last_candle[3],
                    "close": last_candle[4]
                }
                await websocket.send_text(json.dumps(candle_data))
            await asyncio.sleep(1)  # Wait for 1 second before sending the next data
    except WebSocketDisconnect:
        print(f"Client disconnected from {index} WebSocket")
