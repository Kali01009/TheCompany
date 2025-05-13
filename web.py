from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from analyze import start_analysis, get_candles_for_index

app = FastAPI()

selected_indexes = []

@app.get("/", response_class=HTMLResponse)
def index():
    indexes = ["R_10", "R_25", "R_75", "R_100"]
    html = """
    <html>
    <head><title>Volatility Analyzer</title></head>
    <body>
        <h2>Select Indexes to Analyze:</h2>
        <form action="/start" method="post">
    """
    for index in indexes:
        checked = "checked" if index in selected_indexes else ""
        html += f"""
            <label>
                <input type="checkbox" name="indexes" value="{index}" {checked}> {index}
            </label><br>
        """
    html += """
            <button type="submit">Start Analysis</button>
        </form>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/start")
async def start(indexes: list[str] = Form(default=[])):
    global selected_indexes
    selected_indexes = indexes
    start_analysis(selected_indexes)
    return RedirectResponse("/", status_code=303)

@app.get("/candles/{index_name}")
def candles(index_name: str):
    return get_candles_for_index(index_name)

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

