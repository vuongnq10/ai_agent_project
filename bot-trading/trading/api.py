from fastapi import APIRouter
from pydantic import BaseModel
from src.binance_connector.binance import BinanceConnector

trading = APIRouter()


class LeverageRequest(BaseModel):
    symbol: str
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
