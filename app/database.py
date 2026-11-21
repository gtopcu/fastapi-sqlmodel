from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

engine = create_engine(
    settings.sync_database_url,
    echo=False,
    pool_pre_ping=True,
)


def init_db() -> None:
    """Initialize database tables directly if needed (e.g., in tests or standalone runs)."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session]:
    """FastAPI dependency that yields a database session per request."""
    with Session(engine) as session:
        yield session
