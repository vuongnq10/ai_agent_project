import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

from gemini import api

load_dotenv()
app = FastAPI(title="Trading Bot API")

# Mount all /api endpoints here
app.include_router(api.gemini, prefix="/gemini", tags=["API"])

if __name__ == "__main__":
    # Read env vars with fallback defaults
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", 8000))

    uvicorn.run("main:app", host=host, port=port, reload=True)
