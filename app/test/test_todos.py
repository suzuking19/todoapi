import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.database import get_session
from app.models.todo import Todo

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_create_todo(client: TestClient):
    """Test creating a new todo"""
    response = client.post("api/v1/todo", json={
        "title": "New todo",
    })
    assert response.status_code == 200
    todo = response.json()
    assert todo["title"] == "New todo"
    assert todo["completed"] == False
    assert "id" in todo


def test_read_todos(session: Session, client: TestClient):
    """Test reading all todos"""
    # First create a todo
    todo_1 = Todo(title="Test Todo 1")
    todo_2 = Todo(title="Test Todo 2")
    session.add(todo_1)
    session.add(todo_2)
    session.commit()
    
    # Then read all todos
    response = client.get("api/v1/todos")
    assert response.status_code == 200
    todos = response.json()
    assert isinstance(todos, list)
    assert len(todos) >= 2

    # Check that our created todos are in the list and their 'completed' status is false
    for todo in todos:
        if todo["title"] == "Todo 1" or todo["title"] == "Todo 2":
            assert todo["completed"] is False


def test_update_todo(session: Session, client: TestClient):
    """Test toggling a todo's completion status"""
    # First create a todo
    test_todo = Todo(title="Test Todo")
    session.add(test_todo)
    session.commit()
    
    # Toggle the todo
    response = client.patch(f"api/v1/todo/1/toggle")
    assert response.status_code == 200
    updated_todo = response.json()
    assert updated_todo["completed"] == True
    assert updated_todo["id"] == 1


def test_update_todo_not_found(client: TestClient):
    """Test toggling a non-existent todo"""
    response = client.patch("api/v1/todo/99999/toggle")
    assert response.status_code == 404
    assert response.json() == {"detail": "Todo not found"}


def test_delete_completed_todos(session: Session, client: TestClient):
    """Test deleting all completed todos"""
    # Create some todos
    todo_1 = Todo(title="Test Todo 1")
    todo_2 = Todo(title="Test Todo 2")
    session.add(todo_1)
    session.add(todo_2)
    session.commit()
    
    # Get their IDs and toggle one to completed
    todos_response = client.get("api/v1/todos")
    todos = todos_response.json()
    if len(todos) >= 2:
        todo_id = todos[-1]["id"]
        client.patch(f"api/v1/todo/{todo_id}/toggle")
    
    # Delete completed todos
    response = client.delete("api/v1/todos/completed")
    assert response.status_code == 200
    result = response.json()
    assert "ok" in result
    assert "1 completed todos deleted" in result["ok"]


def test_create_todo_invalid_data(client: TestClient):
    """Test creating a todo with invalid data"""
    response = client.post("api/v1/todo", json={})
    # Should fail because title is required
    assert response.status_code == 422