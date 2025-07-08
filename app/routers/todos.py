from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..database import get_session
from ..models.todo import Todo, TodoCreate

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]


@router.post("/todo", response_model=Todo)
def create_todo(todo: TodoCreate, session: SessionDep):
    db_todo = Todo.model_validate(todo)
    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)
    return db_todo


@router.get("/todos", response_model=list[Todo])
def read_todos(session: SessionDep):
    todos = session.exec(select(Todo)).all()
    return todos


@router.patch("/todo/{todo_id}/toggle", response_model=Todo)
def update_todo(todo_id: int, session: SessionDep):
    todo_db = session.get(Todo, todo_id)
    if not todo_db:
        raise HTTPException(status_code=404, detail="Todo not found")
    todo_db.completed = not todo_db.completed
    session.add(todo_db)
    session.commit()
    session.refresh(todo_db)
    return todo_db


@router.delete("/todos/completed")
def delete_completed_todos(session: SessionDep):
    completed_todos = session.exec(select(Todo).where(Todo.completed == True)).all()
    deleted_count = len(completed_todos)
    for todo in completed_todos:
        session.delete(todo)
    session.commit()
    return {"ok": f"{deleted_count} completed todos deleted"}
