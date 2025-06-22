from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Add src to path to import shared modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.hello import get_hello_message, get_hello_message_with_user

app = FastAPI(
    title="POC Backend API",
    description="A FastAPI backend for POC application",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to POC Backend API"}

@app.get("/hello")
async def hello():
    return get_hello_message("FastAPI Backend")

@app.get("/hello/{user_name}")
async def hello_user(user_name: str):
    return get_hello_message_with_user(user_name, "FastAPI Backend")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "poc-backend"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 