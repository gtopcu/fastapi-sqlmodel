from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI, status
from sqlmodel import Session, select

from app.config import settings
from app.database import get_session
from app.routers import companies, employees

# from contextvars import ContextVar
# user_context: ContextVar[str] = ContextVar("user_context")
# token = user_context.set("default")
# try:
#     user_context.get()
# finally:
#     user_context.reset(token)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # Lifespan startup actions (if any)
    yield
    # Lifespan shutdown actions (if any)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# app.state
# app.request.state

# Include routers
app.include_router(companies.router)
app.include_router(employees.router)


@app.get("/", tags=["root"])
def root():
    return {
        "message": "Welcome to FastAPI SQLModel Company & Employee API",
        "docs": "/docs",
        "version": settings.VERSION,
    }


@app.get("/health", tags=["health"], status_code=status.HTTP_200_OK)
def health_check(session: Session = Depends(get_session)):
    """Health check endpoint that verifies database connectivity."""
    try:
        session.exec(select(1)).first()
        return {"status": "healthy", "database": "connected"}
    except Exception as exc:
        return {"status": "unhealthy", "database_error": str(exc)}


def main() -> None:
    """Run server directly via CLI."""
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
