import time
from datetime import date

import pytest
from pydantic import ValidationError
from sqlmodel import Session

from app.crud import company as crud_company
from app.crud import employee as crud_employee
from app.schemas import (
    CompanyCreate,
    CompanyUpdate,
    EmployeeCreate,
    EmployeeUpdate,
)


def test_seeded_data_exists(db_session: Session, seeded_data):
    """Verify that tables were initialized and random data was seeded."""
    companies = seeded_data["companies"]
    employees = seeded_data["employees"]

    assert len(companies) >= 5
    assert len(employees) >= 17

    # Verify querying from database
    db_companies = crud_company.get_companies(db_session, limit=100)
    assert len(db_companies) >= 5
    for c in db_companies:
        assert c.updated is not None

    db_employees = crud_employee.get_employees(db_session, limit=100)
    assert len(db_employees) >= 17
    for e in db_employees:
        assert e.updated is not None


def test_company_crud(db_session: Session):
    """Test full CRUD cycle for Company entity with updated timestamp."""
    # 1. Create
    company_in = CompanyCreate(name="Acme Corporation")
    created = crud_company.create_company(db_session, company_in)
    assert created.id is not None
    assert created.name == "Acme Corporation"
    assert created.updated is not None
    company_id = created.id
    first_updated = created.updated

    # 2. Read by ID
    fetched = crud_company.get_company(db_session, company_id)
    assert fetched is not None
    assert fetched.id == company_id
    assert fetched.name == "Acme Corporation"

    # 3. Read non-existent
    assert crud_company.get_company(db_session, 999999) is None

    # 4. Read list with pagination
    companies_page = crud_company.get_companies(db_session, offset=0, limit=2)
    assert len(companies_page) == 2

    # 5. Update and verify updated timestamp changes
    time.sleep(0.01)
    update_in = CompanyUpdate(name="Acme Global Industries")
    updated = crud_company.update_company(db_session, fetched, update_in)
    assert updated.name == "Acme Global Industries"
    assert updated.updated >= first_updated

    # Verify persistence
    refetched = crud_company.get_company(db_session, company_id)
    assert refetched.name == "Acme Global Industries"
    assert refetched.updated == updated.updated

    # 6. Delete
    crud_company.delete_company(db_session, refetched)
    assert crud_company.get_company(db_session, company_id) is None


def test_employee_crud(db_session: Session):
    """Test full CRUD cycle for Employee entity with updated timestamp."""
    # Setup: Create a company first
    comp = crud_company.create_company(
        db_session, CompanyCreate(name="Tech Innovations")
    )

    # 1. Create with company
    emp_in = EmployeeCreate(
        name="Alice Smith",
        birthday=date(1990, 5, 15),
        company_id=comp.id,
    )
    created = crud_employee.create_employee(db_session, emp_in)
    assert created.id is not None
    assert created.name == "Alice Smith"
    assert created.birthday == date(1990, 5, 15)
    assert created.company_id == comp.id
    assert created.updated is not None
    employee_id = created.id
    first_updated = created.updated

    # 2. Read by ID
    fetched = crud_employee.get_employee(db_session, employee_id)
    assert fetched is not None
    assert fetched.name == "Alice Smith"
    assert fetched.company.id == comp.id

    # 3. Read non-existent
    assert crud_employee.get_employee(db_session, 999999) is None

    # 4. List employees filtered by company
    company_employees = crud_employee.get_employees(db_session, company_id=comp.id)
    assert any(e.id == employee_id for e in company_employees)

    # 5. Update employee and verify updated timestamp changes
    time.sleep(0.01)
    update_in = EmployeeUpdate(
        name="Alice Johnson",
        birthday=date(1990, 5, 20),
    )
    updated = crud_employee.update_employee(db_session, fetched, update_in)
    assert updated.name == "Alice Johnson"
    assert updated.birthday == date(1990, 5, 20)
    assert updated.updated >= first_updated

    # 6. Delete employee
    crud_employee.delete_employee(db_session, updated)
    assert crud_employee.get_employee(db_session, employee_id) is None

    # Company should still exist
    assert crud_company.get_company(db_session, comp.id) is not None


def test_name_length_and_not_null_validations():
    """Verify name fields reject empty strings, >255 characters, and null."""
    # Company validations
    with pytest.raises(ValidationError):
        CompanyCreate(name="")

    with pytest.raises(ValidationError):
        CompanyCreate(name="a" * 256)

    with pytest.raises(ValidationError):
        CompanyCreate(name=None)

    with pytest.raises(ValidationError):
        CompanyUpdate(name="")

    with pytest.raises(ValidationError):
        CompanyUpdate(name="a" * 256)

    # Employee validations
    with pytest.raises(ValidationError):
        EmployeeCreate(name="")

    with pytest.raises(ValidationError):
        EmployeeCreate(name="a" * 256)

    with pytest.raises(ValidationError):
        EmployeeCreate(name=None)

    with pytest.raises(ValidationError):
        EmployeeUpdate(name="")

    with pytest.raises(ValidationError):
        EmployeeUpdate(name="a" * 256)


def test_create_employee_without_company(db_session: Session):
    """Test creating an employee without an assigned company."""
    emp_in = EmployeeCreate(
        name="Freelancer Bob", birthday=date(1985, 3, 10), company_id=None
    )
    created = crud_employee.create_employee(db_session, emp_in)
    assert created.id is not None
    assert created.company_id is None
    assert created.company is None
    assert created.updated is not None


def test_create_employee_invalid_company(db_session: Session):
    """Test creating an employee with a non-existent company ID raises ValueError."""
    emp_in = EmployeeCreate(name="Lost Worker", company_id=999999)
    with pytest.raises(ValueError, match="Company with id 999999 not found"):
        crud_employee.create_employee(db_session, emp_in)


def test_update_employee_invalid_company(db_session: Session):
    """Test updating an employee to a non-existent company ID raises ValueError."""
    emp = crud_employee.create_employee(db_session, EmployeeCreate(name="Valid Worker"))
    update_in = EmployeeUpdate(company_id=999999)
    with pytest.raises(ValueError, match="Company with id 999999 not found"):
        crud_employee.update_employee(db_session, emp, update_in)


def test_one_to_many_relationship(db_session: Session):
    """Verify that a company can have multiple employees and each employee has one company."""
    comp = crud_company.create_company(db_session, CompanyCreate(name="Multi-Emp Corp"))

    emp1 = crud_employee.create_employee(
        db_session, EmployeeCreate(name="Employee One", company_id=comp.id)
    )
    emp2 = crud_employee.create_employee(
        db_session, EmployeeCreate(name="Employee Two", company_id=comp.id)
    )
    emp3 = crud_employee.create_employee(
        db_session, EmployeeCreate(name="Employee Three", company_id=comp.id)
    )

    db_session.refresh(comp)
    assert len(comp.employees) == 3
    emp_ids = [e.id for e in comp.employees]
    assert emp1.id in emp_ids
    assert emp2.id in emp_ids
    assert emp3.id in emp_ids

    # Each employee points back to the single company
    assert emp1.company.id == comp.id
    assert emp2.company.id == comp.id
    assert emp3.company.id == comp.id
