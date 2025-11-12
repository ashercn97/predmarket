from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import time
import random

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/api/polymarket/sweeps")
async def get_sweeps():
    # Mock data for sweeps
    mock_sweeps = {
        "data": [
            {
                "timestamp": int(time.time()) - random.randint(0, 3600),
                "usd_amount": random.randint(100, 100000),
                "outcome": random.choice(["Yes", "No"]),
                "price": random.random(),
                "title": f"Mock Market {random.randint(1, 100)}",
                "market_slug": f"mock-market-{random.randint(1, 100)}",
            }
            for _ in range(50)
        ]
    }
    return mock_sweeps

@app.get("/api/polymarket/expiring")
async def get_expiring():
    # Mock data for expiring markets
    mock_expiring = {
        "data": [
            {
                "hours_until": random.uniform(0.1, 48.0),
                "title": f"Mock Expiring Market {random.randint(1, 100)}",
                "market_slug": f"mock-expiring-market-{random.randint(1, 100)}",
            }
            for _ in range(20)
        ]
    }
    return mock_expiring

# Serve the dashboard
app.mount("/dashboard", StaticFiles(directory="dashboard"), name="dashboard")

@app.get("/")
async def read_index():
    return FileResponse('dashboard/index.html')
