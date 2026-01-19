"""
Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables
from app.routers import auth_router, stocks_router, watchlist_router, ai_router

# Create FastAPI app
app = FastAPI(
    title="Taiwan Stock AI Investment App",
    description="台股 AI 投資建議 APP API",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許所有來源（開發環境）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(stocks_router)
app.include_router(watchlist_router)
app.include_router(ai_router)


@app.on_event("startup")
def on_startup():
    """Create database tables on startup"""
    create_tables()


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Taiwan Stock AI Investment App API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
