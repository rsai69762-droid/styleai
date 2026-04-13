from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers.events import router as events_router
from src.routers.health import router as health_router
from src.routers.recommendations import router as recommendations_router
from src.routers.products import router as products_router
from src.routers.users import router as users_router
from src.routers.wishlist import router as wishlist_router

app = FastAPI(
    title="StylAI API",
    version="0.1.0",
    description="Personalized fashion recommendation API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(products_router, prefix="/api/v1", tags=["products"])
app.include_router(users_router, prefix="/api/v1", tags=["users"])
app.include_router(wishlist_router, prefix="/api/v1", tags=["wishlist"])
app.include_router(events_router, prefix="/api/v1", tags=["events"])
app.include_router(recommendations_router, prefix="/api/v1", tags=["recommendations"])
