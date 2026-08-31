import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from core.exceptions import register_exception_handlers
from core.responses import APIResponse
from api.v1.router import api_router

# Configure structured logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("moneybeing.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} in [{settings.APP_ENV}] mode...")
    try:
        from app.database import Base, engine, SessionLocal
        from database.seed import seed_database
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed_database(db)
        except Exception as e:
            logger.info(f"Database seed notice: {e}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error during startup DB initialization: {e}")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Production-grade Loan Eligibility & Lead Management Backend API with dynamic BRE and Credit Score integration.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Register CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Centralized Exception Handlers
register_exception_handlers(app)

# Include API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", response_model=APIResponse[dict], tags=["System"])
def root_health():
    return APIResponse(
        status="success",
        message=f"{settings.APP_NAME} is running smoothly",
        data={"environment": settings.APP_ENV, "version": "1.0.0"},
    )


@app.get("/", tags=["System"])
def root_redirect():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "documentation": "/docs",
        "api_v1": settings.API_V1_STR,
    }
