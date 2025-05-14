import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import plotly.graph_objects as go
import pandas as pd

from analyze import index_candles  # Ensure this is the correct path where your 'index_candles' is stored.

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
        </style>
    </head>
    <body>
        <div class="chart-container">
            <h1>{index} - Candlestick Chart</h1>
            {chart_html}
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content, status_code=200)

# Ensure to bind to the correct host and port
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))  # Default to 8000 if PORT is not set
    uvicorn.run(app, host="0.0.0.0", port=port)
