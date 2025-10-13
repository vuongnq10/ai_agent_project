import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from gemini import api

app = FastAPI(title="Trading Bot API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify frontend URLs e.g. ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api.gemini, prefix="/gemini", tags=["API"])

if __name__ == "__main__":
    # Read env vars with fallback defaults
    host = os.getenv(config.APP_HOST, "127.0.0.1")
    port = int(os.getenv(config.APP_PORT, 8000))

    uvicorn.run("main:app", host=host, port=port, reload=True)
