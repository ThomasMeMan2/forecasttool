"""
Tests for project management endpoints
"""
import pytest
from fastapi.testclient import TestClient


def test_create_project(client: TestClient):
    """Test creating a new project"""
    response = client.post(
        "/api/projects/",
        json={
            "name": "Test Project",
            "description": "A test project for unit testing",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["description"] == "A test project for unit testing"
    assert "id" in data
    assert data["is_archived"] is False


def test_list_projects(client: TestClient):
    """Test listing projects"""
    # Create a project first
    client.post(
        "/api/projects/",
        json={"name": "Project 1", "description": "First project"},
    )
    client.post(
        "/api/projects/",
        json={"name": "Project 2", "description": "Second project"},
    )

    # List projects
    response = client.get("/api/projects/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] in ["Project 1", "Project 2"]


def test_get_project(client: TestClient):
    """Test getting a specific project"""
    # Create a project
    create_response = client.post(
        "/api/projects/",
        json={"name": "Test Project", "description": "Test description"},
    )
    project_id = create_response.json()["id"]

    # Get the project
    response = client.get(f"/api/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == "Test Project"


def test_update_project(client: TestClient):
    """Test updating a project"""
    # Create a project
    create_response = client.post(
        "/api/projects/",
        json={"name": "Original Name", "description": "Original description"},
    )
    project_id = create_response.json()["id"]

    # Update the project
    response = client.put(
        f"/api/projects/{project_id}",
        json={"name": "Updated Name", "description": "Updated description"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated description"


def test_delete_project(client: TestClient):
    """Test deleting a project"""
    # Create a project
    create_response = client.post(
        "/api/projects/",
        json={"name": "Project to Delete"},
    )
    project_id = create_response.json()["id"]

    # Delete the project
    response = client.delete(f"/api/projects/{project_id}")
    assert response.status_code == 200

    # Verify it's deleted
    get_response = client.get(f"/api/projects/{project_id}")
    assert get_response.status_code == 404


def test_archive_project(client: TestClient):
    """Test archiving a project"""
    # Create a project
    create_response = client.post(
        "/api/projects/",
        json={"name": "Project to Archive"},
    )
    project_id = create_response.json()["id"]

    # Archive the project
    response = client.put(
        f"/api/projects/{project_id}",
        json={"is_archived": True},
    )
    assert response.status_code == 200
    assert response.json()["is_archived"] is True

    # Verify it doesn't appear in default listing
    list_response = client.get("/api/projects/")
    projects = list_response.json()
    assert all(p["id"] != project_id for p in projects)

    # Verify it appears when including archived
    list_archived_response = client.get("/api/projects/?include_archived=true")
    archived_projects = list_archived_response.json()
    assert any(p["id"] == project_id for p in archived_projects)
