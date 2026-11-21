from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlmodel import Session

from app.crud import employee as crud_employee
from app.database import get_session
from app.schemas import (
    EmployeeCreate,
    EmployeeRead,
    EmployeeReadWithCompany,
    EmployeeUpdate,
)

router = APIRouter(prefix="/employees", tags=["employees"])


@router.post(
    "/",
    response_model=EmployeeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an employee",
    description="Create a new employee with validated name (1-255 characters), optional birthday, and company association.",
)
def create_employee(
    employee_in: EmployeeCreate,
    session: Session = Depends(get_session),
) -> EmployeeRead:
    """Create a new employee."""
    try:
        return crud_employee.create_employee(session=session, employee_in=employee_in)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/",
    response_model=list[EmployeeRead],
    summary="List employees",
    description="Retrieve a paginated list of employees with optional company filtering.",
)
def read_employees(
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        default=100, ge=1, le=100, description="Max number of records to return"
    ),
    company_id: int | None = Query(
        default=None, description="Filter employees by associated company ID"
    ),
    session: Session = Depends(get_session),
) -> list[EmployeeRead]:
    """Retrieve all employees with pagination and optional company filter."""
    return crud_employee.get_employees(
        session=session, offset=offset, limit=limit, company_id=company_id
    )


@router.get(
    "/{employee_id}",
    response_model=EmployeeReadWithCompany,
    summary="Get employee by ID",
    description="Retrieve a single employee by ID, including details of the company they belong to.",
)
def read_employee(
    employee_id: int = Path(
        ..., description="The unique integer ID of the employee", ge=1
    ),
    session: Session = Depends(get_session),
) -> EmployeeReadWithCompany:
    """Retrieve a single employee by ID, including company details."""
    employee = crud_employee.get_employee(session=session, employee_id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found",
        )
    return employee


@router.put(
    "/{employee_id}",
    response_model=EmployeeRead,
    summary="Update employee",
    description="Update an employee's details (name, birthday, company). Automatically updates the 'updated' timestamp.",
)
def update_employee(
    employee_id: int = Path(
        ..., description="The unique integer ID of the employee to update", ge=1
    ),
    employee_in: EmployeeUpdate = ...,
    session: Session = Depends(get_session),
) -> EmployeeRead:
    """Update an employee by ID."""
    db_employee = crud_employee.get_employee(session=session, employee_id=employee_id)
    if not db_employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found",
        )
    try:
        return crud_employee.update_employee(
            session=session, db_employee=db_employee, employee_in=employee_in
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete employee",
    description="Delete an employee by ID.",
)
def delete_employee(
    employee_id: int = Path(
        ..., description="The unique integer ID of the employee to delete", ge=1
    ),
    session: Session = Depends(get_session),
) -> None:
    """Delete an employee by ID."""
    db_employee = crud_employee.get_employee(session=session, employee_id=employee_id)
    if not db_employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found",
        )
    crud_employee.delete_employee(session=session, db_employee=db_employee)
