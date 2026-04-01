from typing import List
from fastapi import APIRouter
from pydantic import BaseModel
from src.binance_connector.binance import BinanceConnector

trading = APIRouter()

AI_MODELS = [
    {"id": "gemini", "label": "Gemini", "model": "2.5 Flash"},
    {"id": "claude", "label": "Claude", "model": "Opus 4.6"},
]


@trading.get("/models")
async def get_models():
    return AI_MODELS


class LeverageRequest(BaseModel):
    symbol: str
    leverage: int


class BulkLeverageRequest(BaseModel):
    symbols: List[str]
    leverage: int


@trading.post("/leverage")
async def change_leverage(request: LeverageRequest):
    try:
        connector = BinanceConnector()
        result = connector.set_leverage(request.symbol, request.leverage)
        if result is None:
            return {"success": False, "message": "Failed to set leverage"}
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "message": str(e)}


@trading.post("/leverage/bulk")
async def change_leverage_bulk(request: BulkLeverageRequest):
    connector = BinanceConnector()
    results = []
    for symbol in request.symbols:
        try:
            data = connector.set_leverage(symbol, request.leverage)
            if data is None:
                results.append({"symbol": symbol, "success": False, "message": "Failed to set leverage"})
            else:
                results.append({"symbol": symbol, "success": True, "leverage": data.get("leverage", request.leverage)})
        except Exception as e:
            results.append({"symbol": symbol, "success": False, "message": str(e)})
    return {"results": results}
