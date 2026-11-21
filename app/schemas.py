from datetime import date, datetime

from sqlmodel import Field, SQLModel


# ==========================================
# Company Schemas
# ==========================================
class CompanyBaseSchema(SQLModel):
    name: str = Field(
        min_length=1,
        max_length=255,
        description="Name of the company (1-255 characters)",
    )


class CompanyCreate(CompanyBaseSchema):
    pass


class CompanyUpdate(SQLModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated name of the company (1-255 characters)",
    )


class CompanyRead(CompanyBaseSchema):
    id: int = Field(description="Unique identifier of the company")
    updated: datetime = Field(description="Timestamp when the company was last updated")


# ==========================================
# Employee Schemas
# ==========================================
class EmployeeBaseSchema(SQLModel):
    name: str = Field(
        min_length=1,
        max_length=255,
        description="Full name of the employee (1-255 characters)",
    )
    birthday: date | None = Field(
        default=None,
        description="Birthday of the employee (YYYY-MM-DD)",
    )
    company_id: int | None = Field(
        default=None,
        description="Identifier of the company this employee belongs to",
    )


class EmployeeCreate(EmployeeBaseSchema):
    pass


class EmployeeUpdate(SQLModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated full name of the employee (1-255 characters)",
    )
    birthday: date | None = Field(
        default=None,
        description="Updated birthday of the employee (YYYY-MM-DD)",
    )
    company_id: int | None = Field(
        default=None,
        description="Updated ID of the company this employee belongs to",
    )


class EmployeeRead(EmployeeBaseSchema):
    id: int = Field(description="Unique identifier of the employee")
    updated: datetime = Field(
        description="Timestamp when the employee was last updated"
    )


# ==========================================
# Nested / Relational Schemas
# ==========================================
class CompanyReadWithEmployees(CompanyRead):
    employees: list[EmployeeRead] = Field(
        default=[],
        description="List of employees belonging to this company",
    )


class EmployeeReadWithCompany(EmployeeRead):
    company: CompanyRead | None = Field(
        default=None,
        description="Details of the company this employee belongs to",
    )
