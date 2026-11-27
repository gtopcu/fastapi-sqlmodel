import time

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test API root status and welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["docs"] == "/docs"


def test_health_check_endpoint(client: TestClient):
    """Test database connectivity health check."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_openapi_schema_descriptions(client: TestClient):
    """Verify that OpenAPI documentation contains descriptions for fields."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    openapi = response.json()

    schemas = openapi.get("components", {}).get("schemas", {})
    assert "CompanyCreate" in schemas
    assert "EmployeeCreate" in schemas

    # Check Company properties have descriptions
    company_props = schemas["CompanyCreate"]["properties"]
    assert "description" in company_props["name"]

    # Check Employee properties have descriptions
    emp_props = schemas["EmployeeCreate"]["properties"]
    assert "description" in emp_props["name"]
    assert "description" in emp_props["birthday"]
    assert "description" in emp_props["company_id"]


def test_company_api_crud_flow(client: TestClient):
    """Test full CRUD lifecycle for /companies API endpoints including updated timestamp."""
    # 1. Create company
    create_payload = {"name": "Nexus Dynamics"}
    res = client.post("/companies/", json=create_payload)
    assert res.status_code == 201
    created_company = res.json()
    assert created_company["name"] == "Nexus Dynamics"
    assert "id" in created_company
    assert "updated" in created_company
    company_id = created_company["id"]
    initial_updated = created_company["updated"]

    # 2. Get company by ID
    res = client.get(f"/companies/{company_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == company_id
    assert data["name"] == "Nexus Dynamics"
    assert data["updated"] == initial_updated
    assert "employees" in data
    assert isinstance(data["employees"], list)

    # 3. List companies with pagination
    res = client.get("/companies/?offset=0&limit=5")
    assert res.status_code == 200
    companies_list = res.json()
    assert isinstance(companies_list, list)
    assert len(companies_list) > 0
    assert "updated" in companies_list[0]

    # 4. Update company and check timestamp update
    time.sleep(0.01)
    update_payload = {"name": "Nexus Dynamics International"}
    res = client.put(f"/companies/{company_id}", json=update_payload)
    assert res.status_code == 200
    updated_data = res.json()
    assert updated_data["name"] == "Nexus Dynamics International"
    assert "updated" in updated_data
    assert updated_data["updated"] >= initial_updated

    # 5. Delete company
    res = client.delete(f"/companies/{company_id}")
    assert res.status_code == 204

    # 6. Verify deleted
    res = client.get(f"/companies/{company_id}")
    assert res.status_code == 404


def test_company_api_name_validations(client: TestClient):
    """Test name field validations (1-255 characters, not null) on /companies."""
    # Empty string
    assert client.post("/companies/", json={"name": ""}).status_code == 422

    # Exceeding 255 chars
    long_name = "x" * 256
    assert client.post("/companies/", json={"name": long_name}).status_code == 422

    # Missing name
    assert client.post("/companies/", json={}).status_code == 422

    # Null name
    assert client.post("/companies/", json={"name": None}).status_code == 422

    # Create valid company to test PUT validation
    comp_res = client.post("/companies/", json={"name": "Valid Company"})
    comp_id = comp_res.json()["id"]

    # Update with empty name
    assert client.put(f"/companies/{comp_id}", json={"name": ""}).status_code == 422
    assert (
        client.put(f"/companies/{comp_id}", json={"name": "x" * 256}).status_code == 422
    )


def test_employee_api_crud_flow(client: TestClient):
    """Test full CRUD lifecycle for /employees API endpoints including updated timestamp."""
    # Setup company
    comp_res = client.post("/companies/", json={"name": "CyberTech Labs"})
    assert comp_res.status_code == 201
    comp_id = comp_res.json()["id"]

    # 1. Create employee with company
    emp_payload = {
        "name": "Sarah Connor",
        "birthday": "1984-05-12",
        "company_id": comp_id,
    }
    res = client.post("/employees/", json=emp_payload)
    assert res.status_code == 201
    created_emp = res.json()
    assert created_emp["name"] == "Sarah Connor"
    assert created_emp["birthday"] == "1984-05-12"
    assert created_emp["company_id"] == comp_id
    assert "updated" in created_emp
    emp_id = created_emp["id"]
    initial_updated = created_emp["updated"]

    # 2. Get employee by ID (with company details)
    res = client.get(f"/employees/{emp_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == emp_id
    assert data["name"] == "Sarah Connor"
    assert data["updated"] == initial_updated
    assert data["company"] is not None
    assert data["company"]["id"] == comp_id

    # 3. List employees with company_id filter
    res = client.get(f"/employees/?company_id={comp_id}")
    assert res.status_code == 200
    filtered = res.json()
    assert any(e["id"] == emp_id for e in filtered)
    assert "updated" in filtered[0]

    # 4. Update employee and check updated timestamp
    time.sleep(0.01)
    update_payload = {"name": "Sarah Connor Briggs"}
    res = client.put(f"/employees/{emp_id}", json=update_payload)
    assert res.status_code == 200
    updated_emp = res.json()
    assert updated_emp["name"] == "Sarah Connor Briggs"
    assert "updated" in updated_emp
    assert updated_emp["updated"] >= initial_updated

    # 5. Delete employee
    res = client.delete(f"/employees/{emp_id}")
    assert res.status_code == 204

    # 6. Verify employee deleted
    res = client.get(f"/employees/{emp_id}")
    assert res.status_code == 404


def test_employee_api_name_validations(client: TestClient):
    """Test name field validations (1-255 characters, not null) on /employees."""
    # Empty string
    assert client.post("/employees/", json={"name": ""}).status_code == 422

    # Exceeding 255 chars
    assert client.post("/employees/", json={"name": "a" * 256}).status_code == 422

    # Missing name
    assert client.post("/employees/", json={}).status_code == 422

    # Null name
    assert client.post("/employees/", json={"name": None}).status_code == 422

    # Create valid employee to test PUT validation
    emp_res = client.post("/employees/", json={"name": "Valid Emp"})
    emp_id = emp_res.json()["id"]

    assert client.put(f"/employees/{emp_id}", json={"name": ""}).status_code == 422
    assert (
        client.put(f"/employees/{emp_id}", json={"name": "a" * 256}).status_code == 422
    )


def test_employee_api_invalid_company(client: TestClient):
    """Test creating and updating employee with non-existent company returns 404."""
    res = client.post(
        "/employees/",
        json={"name": "Orphan Employee", "company_id": 999999},
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()

    create_res = client.post("/employees/", json={"name": "Valid Worker"})
    emp_id = create_res.json()["id"]

    update_res = client.put(f"/employees/{emp_id}", json={"company_id": 999999})
    assert update_res.status_code == 404
    assert "not found" in update_res.json()["detail"].lower()


def test_id_autogenerated_and_not_taken_from_input(client: TestClient):
    """Verify that ID fields are autogenerated by the database and cannot be supplied via API input."""
    # Attempt to supply an arbitrary ID when creating a company
    comp_res = client.post(
        "/companies/",
        json={"id": 999999, "name": "Autogenerated ID Corp"},
    )
    assert comp_res.status_code == 201
    comp_data = comp_res.json()
    assert "id" in comp_data
    assert comp_data["id"] != 999999
    assert isinstance(comp_data["id"], int)
    assert comp_data["id"] > 0
    generated_comp_id = comp_data["id"]

    # Attempt to supply an arbitrary ID when creating an employee
    emp_res = client.post(
        "/employees/",
        json={
            "id": 888888,
            "name": "Autogenerated ID Employee",
            "company_id": generated_comp_id,
        },
    )
    assert emp_res.status_code == 201
    emp_data = emp_res.json()
    assert "id" in emp_data
    assert emp_data["id"] != 888888
    assert isinstance(emp_data["id"], int)
    assert emp_data["id"] > 0
    assert emp_data["company_id"] == generated_comp_id
