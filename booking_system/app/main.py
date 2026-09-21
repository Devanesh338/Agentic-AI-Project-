from fastapi import FastAPI
from app.api import booking_routes
from app.database.database import engine, Base
import os
from fastapi.staticfiles import StaticFiles

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Travel Booking System API", version="1.0.0")

app.include_router(booking_routes.router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Mount static files (serve JS, CSS, and index.html at root)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
