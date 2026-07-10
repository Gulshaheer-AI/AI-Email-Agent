import uvicorn
from fastapi import FastAPI
from config.database import engine
from models import schemas
from api import webhooks

#  https://slingshot-illusive-vanity.ngrok-free.dev

# Connect schemas to the engine to build tables on startup if they don't exist
schemas.Base.metadata.create_all(bind=engine)

# Initialize application
app = FastAPI(
    title="Autonomous Email Operations Agent Backend",
    version="1.0.0",
    description="Production-grade AI agent architecture using FastAPI, SQLAlchemy, and Gemini."
)

# Mount the webhook router
app.include_router(webhooks.router)

@app.get("/health", tags=["System Health"])
def system_health_check() -> dict:
    """Basic endpoint to verify the API server is up and responsive."""
    return {"status": "healthy", "service": "email_agent_backend"}

if __name__ == "__main__":
    # Run the server locally using uvicorn on port 8000
    uvicorn.run("main.py:app", host="127.0.0.1", port=8000, reload=True)