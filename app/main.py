"""Main FastAPI application with Scalar documentation."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import settings
from app.core.logging import setup_logging
from app.database import db_manager
from app.routers.deps import get_db
from app.middleware.error_handler import error_handler_middleware
from app.middleware.logging_middleware import logging_middleware
from app.routers.webhooks.kapso import router as kapso_router
from app.api.v1.router import api_router

# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    - Startup: Initialize database engine and session factory
    - Shutdown: Dispose database engine and close all connections
    """
    # Startup: Connect to database
    await db_manager.connect()
    yield
    await db_manager.disconnect()


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url=None,  # Disable default docs
    redoc_url=settings.REDOC_URL,
    openapi_url=settings.OPENAPI_URL,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add custom middlewares
app.middleware("http")(logging_middleware)
app.middleware("http")(error_handler_middleware)

# Include API routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(kapso_router)


# Scalar documentation endpoint
@app.get("/docs", include_in_schema=False)
async def scalar_html() -> HTMLResponse:
    """Scalar API documentation UI.

    Returns:
        HTMLResponse: HTML page with Scalar documentation
    """
    return HTMLResponse(
        content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{settings.APP_NAME} - API Documentation</title>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
        </head>
        <body>
            <script
                id="api-reference"
                data-url="{settings.OPENAPI_URL}"
                data-configuration='{{"theme":"purple","layout":"modern","defaultOpenAllTags":true}}'
            ></script>
            <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
        </body>
        </html>
        """,
        status_code=200,
    )
