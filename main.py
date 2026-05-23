import os
from dataclasses import dataclass, field
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.utils.logging import logger


@dataclass
class AppConfig:
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("PORT", 8000))
    DEBUG: bool = os.environ.get("DEBUG", "false").lower() in ("1", "true", "yes")
    # Comma-separated origins or '*' for all. Example: 'http://localhost:3000,https://example.com'
    ALLOWED_ORIGINS: List[str] = field(
        default_factory=lambda: (
            os.environ.get("ALLOWED_ORIGINS", "*").split(",")
            if os.environ.get("ALLOWED_ORIGINS")
            else ["*"]
        )
    )


config = AppConfig()


app = FastAPI(
    title="FraudShield AI",
    description="Real-time fraud detection — ML prediction + LLM reasoning",
    version="1.0.0",
)

# Allow the frontend (Streamlit / React on configured origins) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,  # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
async def startup():
    logger.info(f"FraudShield AI API started on {config.HOST}:{config.PORT} (debug={config.DEBUG})")


@app.on_event("shutdown")
async def shutdown():
    logger.info("FraudShield AI API shutting down.")



# 8. Main Entrypoint
if __name__ == "__main__":
    import uvicorn

    logger.info(f"Launching server on {config.HOST}:{config.PORT}")
    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=config.DEBUG)