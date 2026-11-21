from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlmodel import Session

from app.crud import company as crud_company
from app.database import get_session
from app.schemas import (
    CompanyCreate,
    CompanyRead,
    CompanyReadWithEmployees,
    CompanyUpdate,
)

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post(
    "/",
    response_model=CompanyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a company",
    description="Create a new company with a validated name (1-255 characters).",
)
def create_company(
    company_in: CompanyCreate,
    session: Session = Depends(get_session),
) -> CompanyRead:
    """Create a new company."""
    return crud_company.create_company(session=session, company_in=company_in)


@router.get(
    "/",
    response_model=list[CompanyRead],
    summary="List companies",
    description="Retrieve a paginated list of companies.",
)
def read_companies(
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        default=100, ge=1, le=100, description="Max number of records to return"
    ),
    session: Session = Depends(get_session),
) -> list[CompanyRead]:
    """Retrieve all companies with pagination."""
    return crud_company.get_companies(session=session, offset=offset, limit=limit)


@router.get(
    "/{company_id}",
    response_model=CompanyReadWithEmployees,
    summary="Get company by ID",
    description="Retrieve a single company by ID, including its associated employees list.",
)
def read_company(
    company_id: int = Path(
        ..., description="The unique integer ID of the company", ge=1
    ),
    session: Session = Depends(get_session),
) -> CompanyReadWithEmployees:
    """Retrieve a single company by ID, including its associated employees."""
    company = crud_company.get_company(session=session, company_id=company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with id {company_id} not found",
        )
    return company


@router.put(
    "/{company_id}",
    response_model=CompanyRead,
    summary="Update company",
    description="Update an existing company by ID. Automatically updates the 'updated' timestamp.",
)
def update_company(
    company_id: int = Path(
        ..., description="The unique integer ID of the company to update", ge=1
    ),
    company_in: CompanyUpdate = ...,
    session: Session = Depends(get_session),
) -> CompanyRead:
    """Update a company by ID."""
    db_company = crud_company.get_company(session=session, company_id=company_id)
    if not db_company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with id {company_id} not found",
        )
    return crud_company.update_company(
        session=session, db_company=db_company, company_in=company_in
    )


@router.delete(
    "/{company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete company",
    description="Delete a company by ID and cascade delete any associated employees.",
)
def delete_company(
    company_id: int = Path(
        ..., description="The unique integer ID of the company to delete", ge=1
    ),
    session: Session = Depends(get_session),
) -> None:
    """Delete a company by ID."""
    db_company = crud_company.get_company(session=session, company_id=company_id)
    if not db_company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with id {company_id} not found",
        )
    crud_company.delete_company(session=session, db_company=db_company)
