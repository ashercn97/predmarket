from fastapi import FastAPI
from predmarket.client import UnifiedClient
from predmarket.kalshi.rest import KalshiRest
from predmarket.polymarket.rest import PolymarketRest
import httpx
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/questions")
async def get_questions():
    async with httpx.AsyncClient() as client:
        kalshi = KalshiRest(client)
        polymarket = PolymarketRest(client)
        unified_client = UnifiedClient(kalshi, polymarket)
        questions = await unified_client.fetch_questions()
        return questions

@app.get("/contracts")
async def get_contracts():
    async with httpx.AsyncClient() as client:
        kalshi = KalshiRest(client)
        polymarket = PolymarketRest(client)
        unified_client = UnifiedClient(kalshi, polymarket)
        contracts = await unified_client.fetch_contracts()
        return contracts
