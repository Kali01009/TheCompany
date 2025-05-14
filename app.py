import os
import web

urls = (
    '/', 'Index'
)

class Index:
    def GET(self):
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Volatility 75 - Live Candlestick Chart</title>
    <script src="https://cdn.plot.ly/plotly-2.31.1.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background-color: #fafafa; }
        h2 { margin-bottom: 20px; }
        #chart { width: 100%; height: 600px; }
        table { width: 100%; border-collapse: collapse; margin-top: 30px; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
        th { background-color: #eee; }
    </style>
</head>
<body>
    <h2>Volatility 75 Index (R_75) - Live Candlestick Chart</h2>
    <div id="chart"></div>

    <table id="ohlc-table">
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
        const ws = new WebSocket("wss://ws.binaryws.com/websockets/v3?app_id=1089");

        let times = [], opens = [], highs = [], lows = [], closes = [];
        let lastCandleTime = null;

        ws.onopen = () => {
            ws.send(JSON.stringify({ ticks: "R_75", subscribe: 1 }));
            ws.send(JSON.stringify({
                ticks_history: "R_75",
                style: "candles",
                granularity: 60,
                count: 50,
                end: "latest",
                start: 1
            }));
        };

        ws.onmessage = (msg) => {
            const data = JSON.parse(msg.data);

            if (data.candles) {
                for (let candle of data.candles) {
                    const time = new Date(candle.epoch * 1000).toLocaleTimeString();
                    times.push(time);
                    opens.push(candle.open);
                    highs.push(candle.high);
                    lows.push(candle.low);
                    closes.push(candle.close);
                }
                lastCandleTime = Math.floor(data.candles[data.candles.length - 1].epoch / 60) * 60;
                Plotly.newPlot("chart", [{
                    x: times,
                    open: opens,
                    high: highs,
                    low: lows,
                    close: closes,
                    type: 'candlestick',
                    name: 'R_75'
                }], {
                    title: "Volatility 75 (R_75)",
                    xaxis: { title: 'Time' },
                    yaxis: { title: 'Price' }
                });
                updateTable();
            }

            if (data.tick) {
                const price = data.tick.quote;
                const epoch = data.tick.epoch;
                const minute = Math.floor(epoch / 60) * 60;
                const time = new Date(minute * 1000).toLocaleTimeString();

                if (minute !== lastCandleTime) {
                    times.push(time);
                    opens.push(price);
                    highs.push(price);
                    lows.push(price);
                    closes.push(price);
                    lastCandleTime = minute;
                    if (times.length > 50) {
                        times.shift(); opens.shift(); highs.shift(); lows.shift(); closes.shift();
                    }
                } else {
                    let idx = times.length - 1;
                    highs[idx] = Math.max(highs[idx], price);
                    lows[idx] = Math.min(lows[idx], price);
                    closes[idx] = price;
                }

                Plotly.update("chart", {
                    x: [times],
                    open: [opens],
                    high: [highs],
                    low: [lows],
                    close: [closes]
                });
                updateTable();
            }
        };

        function updateTable() {
            const tbody = document.querySelector("#ohlc-table tbody");
            tbody.innerHTML = "";
            for (let i = times.length - 1; i >= 0; i--) {
                const row = `<tr>
                    <td>${times[i]}</td>
                    <td>${opens[i].toFixed(5)}</td>
                    <td>${highs[i].toFixed(5)}</td>
                    <td>${lows[i].toFixed(5)}</td>
                    <td>${closes[i].toFixed(5)}</td>
                </tr>`;
                tbody.innerHTML += row;
            }
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app = web.application(urls, globals())
    port = int(os.environ.get("PORT", 5000))
    web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", port))
