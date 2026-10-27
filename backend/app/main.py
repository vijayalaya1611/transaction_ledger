from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.database import init_db
from app.routers import accounts, transactions, transfers

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist
    await init_db()
    yield
    # Shutdown logic if any

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-ready Transaction Ledger API featuring ACID transactions, optimistic/pessimistic locking, idempotency, and money transfers.",
    lifespan=lifespan
)

# CORS Middleware setup
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standardized Validation Error Handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = " -> ".join([str(p) for p in err.get("loc", []) if p != "body"])
        errors.append(f"{loc}: {err.get('msg')}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Invalid request parameters or payload",
            "details": errors
        }
    )

# Include Routers
app.include_router(accounts.router, prefix=settings.API_V1_PREFIX)
app.include_router(transactions.router, prefix=settings.API_V1_PREFIX)
app.include_router(transfers.router, prefix=settings.API_V1_PREFIX)

@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "docs_url": "/docs",
        "api_prefix": settings.API_V1_PREFIX
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
