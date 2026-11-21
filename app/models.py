from datetime import UTC, date, datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel


class CompanyBase(SQLModel):
    name: str = Field(
        min_length=1,
        max_length=255,
        index=True,
        nullable=False,
        description="Name of the company (1-255 characters)",
    )


class Company(CompanyBase, table=True):
    __tablename__ = "companies"

    id: int | None = Field(
        default=None,
        primary_key=True,
        description="Unique identifier of the company",
    )
    updated: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
        description="Timestamp when the company was last updated",
    )
    employees: list[Employee] = Relationship(
        back_populates="company",
        cascade_delete=True,
    )


class EmployeeBase(SQLModel):
    name: str = Field(
        min_length=1,
        max_length=255,
        index=True,
        nullable=False,
        description="Full name of the employee (1-255 characters)",
    )
    birthday: date | None = Field(
        default=None,
        description="Birthday of the employee (YYYY-MM-DD)",
    )
    company_id: int | None = Field(
        default=None,
        foreign_key="companies.id",
        ondelete="CASCADE",
        description="Identifier of the company this employee belongs to",
    )


class Employee(EmployeeBase, table=True):
    __tablename__ = "employees"

    id: int | None = Field(
        default=None,
        primary_key=True,
        description="Unique identifier of the employee",
    )
    updated: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
        description="Timestamp when the employee was last updated",
    )
    company: Company | None = Relationship(back_populates="employees")
