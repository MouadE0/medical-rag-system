from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router
from .auth_routes import router as auth_router
from ..config import settings

app = FastAPI(
    title="Medical RAG - CIM-10 Code Suggester",
    description="RAG system for suggesting CIM-10 codes based on medical queries using CoCoA",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(router, prefix="/api/v1", tags=["codes"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Medical RAG API - CIM-10 Code Suggester",
        "docs": "/docs",
        "version": "1.0.0",
        "authentication": "JWT Bearer Token required for /api/v1/suggest-codes and /api/v1/lookup-code"
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )