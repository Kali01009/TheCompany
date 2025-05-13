from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from analyze import start_analysis, index_candles

app = FastAPI()

@app.get("/")
def root():
    return {"message": "📊 Volatility Analyzer is running."}

@app.post("/start")
def start(indexes: str = Form(...)):
    try:
        symbols = indexes.split(",")
        start_analysis(symbols)
        return {"status": "started", "symbols": symbols}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/candles/{index}")
def get_candles(index: str):
    data = index_candles.get(index)
    if not data:
        return JSONResponse(content={"error": "No data for index"}, status_code=404)
    candles = [
        {"timestamp": c[0], "open": c[1], "high": c[2], "low": c[3], "close": c[4]}
        for c in data[-50:]
    ]
    return {"index": index, "candles": candles}
