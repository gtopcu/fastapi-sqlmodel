import os
import shutil
import subprocess
import time
import uuid
from collections.abc import Generator
from typing import Any

import pytest
from alembic.config import Config
from faker import Faker
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine

from alembic import command
from app.database import get_session
from app.main import app
from app.models import Company, Employee

fake = Faker()


def find_docker_bin() -> str:
    """Find docker executable path."""
    docker_bin = shutil.which("docker")
    if docker_bin:
        return docker_bin
    common_paths = [
        "/Users/hukanege/.docker/bin/docker",
        "/usr/local/bin/docker",
        "/opt/homebrew/bin/docker",
        "/usr/bin/docker",
    ]
    for p in common_paths:
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p
    raise RuntimeError("Docker binary not found on the system")


@pytest.fixture(scope="session")
def postgres_container() -> Generator[str]:
    """
    Session fixture that spins up a fresh postgres:18 Docker container,
    waits for it to become healthy, yields the database connection URL,
    and destroys the container upon session teardown.
    """
    # Allow override via environment variable if requested
    env_url = os.environ.get("TEST_DATABASE_URL")
    if env_url:
        yield env_url
        return

    docker_bin = find_docker_bin()
    container_name = f"test_pg18_{uuid.uuid4().hex[:8]}"
    db_name = "test_db"
    db_user = "postgres"
    db_password = "postgres"

    print(f"\n[Docker] Starting PostgreSQL 18 container: {container_name}...")
    run_cmd = [
        docker_bin,
        "run",
        "-d",
        "--name",
        container_name,
        "-e",
        f"POSTGRES_PASSWORD={db_password}",
        "-e",
        f"POSTGRES_USER={db_user}",
        "-e",
        f"POSTGRES_DB={db_name}",
        "-p",
        "127.0.0.1::5432",
        "postgres:18",
    ]
    subprocess.run(run_cmd, check=True)

    try:
        # Determine mapped host port
        host_port = None
        for _ in range(10):
            try:
                port_output = subprocess.check_output(
                    [docker_bin, "port", container_name, "5432"], text=True
                ).strip()
                host_port = port_output.split("\n")[0].split(":")[-1]
                if host_port:
                    break
            except Exception:
                time.sleep(0.3)

        if not host_port:
            raise RuntimeError(f"Could not retrieve mapped port for {container_name}")

        db_url = f"postgresql+psycopg://{db_user}:{db_password}@127.0.0.1:{host_port}/{db_name}"

        # Wait for PostgreSQL to be completely ready and accepting queries
        max_attempts = 40
        ready = False
        import psycopg

        for attempt in range(1, max_attempts + 1):
            try:
                # Also ensure container logs show ready to accept connections
                logs = subprocess.check_output(
                    [docker_bin, "logs", container_name], text=True
                )
                if (
                    "PostgreSQL init process complete; ready for start up." in logs
                    and "database system is ready to accept connections" in logs
                ):
                    with psycopg.connect(
                        f"postgresql://{db_user}:{db_password}@127.0.0.1:{host_port}/{db_name}",
                        connect_timeout=2,
                    ) as conn:
                        with conn.cursor() as cur:
                            cur.execute("SELECT 1")
                            ready = True
                            print(f"[Docker] PostgreSQL 18 ready on attempt {attempt}")
                            break
            except Exception:
                pass
            time.sleep(0.5)

        if not ready:
            raise RuntimeError(
                f"PostgreSQL 18 container {container_name} failed to become ready in time."
            )

        print(f"[Docker] Database URL: {db_url}")

        yield db_url

    finally:
        print(f"\n[Docker] Destroying PostgreSQL 18 container: {container_name}...")
        subprocess.run(
            [docker_bin, "stop", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            [docker_bin, "rm", "-f", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"[Docker] PostgreSQL 18 container {container_name} destroyed.")


@pytest.fixture(scope="session")
def test_engine(postgres_container: str):
    """
    Creates a SQLModel/SQLAlchemy engine, initializes database tables
    using Alembic migrations, and disposes connection pool at session end.
    """
    db_url = postgres_container

    # Run Alembic migrations against the fresh PostgreSQL instance
    print("\n[Alembic] Running migrations upgrade head on test database...")
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")
    print("[Alembic] Migrations completed.")

    engine = create_engine(db_url, echo=False, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def seeded_data(test_engine) -> dict[str, list[Any]]:
    """
    Seeds the test database with random companies and employees using Faker.
    Returns the created entities for assertions in tests.
    """
    print("\n[Seeding] Adding random data (companies & employees)...")
    companies = []
    employees = []

    with Session(test_engine) as session:
        # Create 5 random companies
        for _ in range(5):
            comp = Company(name=f"{fake.company()} {fake.company_suffix()}")
            session.add(comp)
            companies.append(comp)
        session.commit()
        for comp in companies:
            session.refresh(comp)

        # Create 15 random employees assigned to companies
        for i in range(15):
            comp = companies[i % len(companies)]
            emp = Employee(
                name=fake.name(),
                birthday=fake.date_of_birth(minimum_age=20, maximum_age=60),
                company_id=comp.id,
            )
            session.add(emp)
            employees.append(emp)

        # Create 2 employees without a company
        for _ in range(2):
            emp = Employee(
                name=fake.name(),
                birthday=fake.date_of_birth(minimum_age=22, maximum_age=50),
                company_id=None,
            )
            session.add(emp)
            employees.append(emp)

        session.commit()
        for emp in employees:
            session.refresh(emp)

    print(f"[Seeding] Added {len(companies)} companies and {len(employees)} employees.")
    return {"companies": companies, "employees": employees}


@pytest.fixture
def db_session(test_engine, seeded_data) -> Generator[Session]:
    """
    Provides a database session for unit tests, ensuring the test
    database has tables initialized and random data seeded.
    """
    with Session(test_engine) as session:
        yield session


@pytest.fixture(scope="session")
def client(test_engine, seeded_data) -> Generator[TestClient]:
    """
    Provides a FastAPI TestClient configured to use the PostgreSQL test container.
    """

    def override_get_session() -> Generator[Session]:
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
