from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
import json
import os
import asyncio
from analyze import index_candles

# Assume index_candles is a dict: { 'INDEX_NAME': [ {time, open, high, low, close}, ... ] }

app = FastAPI()

@app.get("/")
async def root():
    indices = list(index_candles.keys())
    # Create list items for each index
    items = "".join([f'<li><a href="/chart/{idx}">{idx}</a></li>' for idx in indices])
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Available Indices</title>
    </head>
    <body>
        <h1>Available Indices</h1>
        <ul>
            {items}
        </ul>
    </body>
    </html>
    """
    return HTMLResponse(html_content)

@app.get("/chart/{index_name}")
async def chart(index_name: str):
    if index_name not in index_candles:
        return HTMLResponse(f"<h1>Index '{index_name}' not found</h1>", status_code=404)
    # Get the latest 50 candles for initial display
    candles = index_candles[index_name][-50:]
    # Convert data to JSON for embedding in page
    data_json = json.dumps(candles)
    # HTML content with Plotly and WebSocket
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Candlestick Chart - {index_name}</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            #chart {{ width: 100%; height: 60vh; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: right; }}
            th {{ background-color: #f2f2f2; }}
            td:first-child, th:first-child {{ text-align: left; }}
        </style>
    </head>
    <body>
        <h1>Candlestick Chart for {index_name}</h1>
        <div id="chart"></div>
        <table id="data-table">
            <thead>
                <tr><th>Time</th><th>Open</th><th>High</th><th>Low</th><th>Close</th></tr>
            </thead>
            <tbody></tbody>
        </table>
        <script>
            var indexName = {json.dumps(index_name)};
            var initialData = {data_json};
            // Create table from initial data
            function addRow(candle) {{
                var tbody = document.getElementById('data-table').getElementsByTagName('tbody')[0];
                var row = tbody.insertRow();
                var cellTime = row.insertCell(0);
                cellTime.innerText = candle.time;
                var cellOpen = row.insertCell(1);
                cellOpen.innerText = candle.open;
                var cellHigh = row.insertCell(2);
                cellHigh.innerText = candle.high;
                var cellLow = row.insertCell(3);
                cellLow.innerText = candle.low;
                var cellClose = row.insertCell(4);
                cellClose.innerText = candle.close;
            }}
            // Populate initial table
            for (var i = 0; i < initialData.length; i++) {{
                addRow(initialData[i]);
            }}
            // Plot initial candlestick chart
            var times = initialData.map(x => x.time);
            var opens = initialData.map(x => x.open);
            var highs = initialData.map(x => x.high);
            var lows = initialData.map(x => x.low);
            var closes = initialData.map(x => x.close);
            var trace = {{
                x: times,
                open: opens,
                high: highs,
                low: lows,
                close: closes,
                type: 'candlestick',
                name: indexName
            }};
            var layout = {{
                title: 'Candlestick chart for ' + indexName,
                xaxis: {{title: 'Time'}},
                yaxis: {{title: 'Price'}}
            }};
            Plotly.newPlot('chart', [trace], layout);
            // Setup WebSocket connection
            var ws_scheme = window.location.protocol === "https:" ? "wss://" : "ws://";
            var socket = new WebSocket(ws_scheme + window.location.host + '/ws/' + indexName);
            socket.onmessage = function(event) {{
                var newData = JSON.parse(event.data);
                // newData could be a list of candles
                newData.forEach(function(candle) {{
                    // Add new data to table
                    addRow(candle);
                    // Maintain only latest 50 rows
                    var tbody = document.getElementById('data-table').getElementsByTagName('tbody')[0];
                    if (tbody.rows.length > 50) {{
                        tbody.deleteRow(0);
                    }}
                    // Update chart data
                    initialData.push(candle);
                    if (initialData.length > 50) {{
                        initialData.shift();
                    }}
                }});
                // Redraw chart with updated data
                var times = initialData.map(x => x.time);
                var opens = initialData.map(x => x.open);
                var highs = initialData.map(x => x.high);
                var lows = initialData.map(x => x.low);
                var closes = initialData.map(x => x.close);
                Plotly.react('chart', [{{
                    x: times, open: opens, high: highs, low: lows, close: closes,
                    type: 'candlestick', name: indexName
                }}], layout);
            }};
            socket.onclose = function(event) {{
                console.log('WebSocket closed');
            }};
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html_content)

@app.websocket("/ws/{index_name}")
async def websocket_endpoint(websocket: WebSocket, index_name: str):
    if index_name not in index_candles:
        await websocket.close()
        return
    await websocket.accept()
    prev_len = len(index_candles[index_name])
    try:
        while True:
            await asyncio.sleep(1)
            current_len = len(index_candles[index_name])
            if current_len > prev_len:
                new_candles = index_candles[index_name][prev_len:current_len]
                # Send new candles as JSON text
                await websocket.send_text(json.dumps(new_candles))
                prev_len = current_len
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for index: {index_name}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
