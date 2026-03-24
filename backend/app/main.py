from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import auth, search, rulings, bookmarks


app = FastAPI(
    title=settings.app_name,
    description="Thai Law & Court Ruling Search Platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://lawfi.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(rulings.router, prefix="/api/rulings", tags=["rulings"])
app.include_router(bookmarks.router, prefix="/api/bookmarks", tags=["bookmarks"])


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": settings.app_name}
