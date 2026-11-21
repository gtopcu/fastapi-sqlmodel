from datetime import UTC, datetime

from sqlmodel import Session, select

from app.models import Company
from app.schemas import CompanyCreate, CompanyUpdate


def create_company(session: Session, company_in: CompanyCreate) -> Company:
    """Create a new company in the database."""
    db_company = Company.model_validate(company_in)
    session.add(db_company)
    session.commit()
    session.refresh(db_company)
    return db_company


def get_company(session: Session, company_id: int) -> Company | None:
    """Retrieve a single company by ID."""
    return session.get(Company, company_id)


def get_companies(session: Session, offset: int = 0, limit: int = 100) -> list[Company]:
    """Retrieve multiple companies with pagination."""
    statement = select(Company).offset(offset).limit(limit)
    return list(session.exec(statement).all())


def update_company(
    session: Session,
    db_company: Company,
    company_in: CompanyUpdate,
) -> Company:
    """Update an existing company and update the timestamp."""
    company_data = company_in.model_dump(exclude_unset=True)
    db_company.sqlmodel_update(company_data)
    db_company.updated = datetime.now(UTC)
    session.add(db_company)
    session.commit()
    session.refresh(db_company)
    return db_company


def delete_company(session: Session, db_company: Company) -> None:
    """Delete a company from the database."""
    session.delete(db_company)
    session.commit()
