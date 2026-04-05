# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.routers import (
    badge_route,
    gamification_route,
    job_route,
    message_route,
    offer_route,
    reputation_route,
    user_skill_route,
    ai_route,
)
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Kintsugi API",
    description="Repair marketplace with AI diagnosis and community trust.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(badge_route.router)
app.include_router(ai_route.router)
app.include_router(gamification_route.router)
app.include_router(job_route.router)
# app.include_router(message_route.router)
app.include_router(offer_route.router)
app.include_router(reputation_route.router)
app.include_router(user_skill_route.router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Kintsugi API",
        version="1.0.0",
        description="Repair marketplace with AI diagnosis and community trust.",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
