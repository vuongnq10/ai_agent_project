import os
import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from routers.stream import stream
from routers.trading import trading
from connectors.telegram import listen_messages


@asynccontextmanager
async def lifespan(_: FastAPI):
    asyncio.create_task(listen_messages())
    yield


app = FastAPI(title="Trading Bot API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify frontend URLs e.g. ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stream, tags=["Stream"])
app.include_router(trading, prefix="/trading", tags=["Trading"])

if __name__ == "__main__":
    # Read env vars with fallback defaults
    host = os.getenv(config.APP_HOST, "127.0.0.1")
    port = int(os.getenv(config.APP_PORT, "8000"))

    uvicorn.run("main:app", host=host, port=port, reload=True)
