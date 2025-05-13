from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "🚀 WebSocket breakout bot is running!"}

# Make sure this runs only when `web.py` is the entry point
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("web:app", host="0.0.0.0", port=port)
