from datetime import UTC, datetime

from sqlmodel import Session, select

from app.models import Company, Employee
from app.schemas import EmployeeCreate, EmployeeUpdate


def create_employee(session: Session, employee_in: EmployeeCreate) -> Employee:
    """Create a new employee in the database."""
    if employee_in.company_id is not None:
        company = session.get(Company, employee_in.company_id)
        if not company:
            raise ValueError(f"Company with id {employee_in.company_id} not found")

    db_employee = Employee.model_validate(employee_in)
    session.add(db_employee)
    session.commit()
    session.refresh(db_employee)
    return db_employee


def get_employee(session: Session, employee_id: int) -> Employee | None:
    """Retrieve an employee by ID."""
    return session.get(Employee, employee_id)


def get_employees(
    session: Session,
    offset: int = 0,
    limit: int = 100,
    company_id: int | None = None,
) -> list[Employee]:
    """Retrieve a list of employees with pagination and optional company filter."""
    statement = select(Employee)
    if company_id is not None:
        statement = statement.where(Employee.company_id == company_id)
    statement = statement.offset(offset).limit(limit)
    return list(session.exec(statement).all())


def update_employee(
    session: Session,
    db_employee: Employee,
    employee_in: EmployeeUpdate,
) -> Employee:
    """Update an existing employee and update the timestamp."""
    update_data = employee_in.model_dump(exclude_unset=True)

    if "company_id" in update_data and update_data["company_id"] is not None:
        company = session.get(Company, update_data["company_id"])
        if not company:
            raise ValueError(f"Company with id {update_data['company_id']} not found")

    db_employee.sqlmodel_update(update_data)
    db_employee.updated = datetime.now(UTC)
    session.add(db_employee)
    session.commit()
    session.refresh(db_employee)
    return db_employee


def delete_employee(session: Session, db_employee: Employee) -> None:
    """Delete an employee from the database."""
    session.delete(db_employee)
    session.commit()
