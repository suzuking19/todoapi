from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from sqlmodel import Field, Session, SQLModel, create_engine, select

from .routers import common 

class TodoBase(SQLModel):
    title: str = Field(..., min_length=1, max_length=10)

class Todo(TodoBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    compoleted: bool = Field(default=False)

class TodoCreate(TodoBase):
    pass

DATABASE_URL = "sqlite:///todo.db"
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield 

SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI(lifespan=lifespan)

app.include_router(common.router, tags=["common"])

@app.post("/todo", response_model=Todo)
def create_todo(todo: TodoCreate, session: SessionDep):
    db_todo = Todo.model_validate(todo)
    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)
    return db_todo

@app.get("/todos", response_model=list[Todo])
def read_todos(session: SessionDep):
    todos = session.exec(select(Todo)).all()
    return todos

@app.patch("/todo/{todo_id}/toggle", response_model=Todo)
def update_todo(todo_id: int, session: SessionDep):
    todo_db = session.get(Todo, todo_id)
    if not todo_db:
        raise HTTPException(status_code=404, detail="Todo not found")
    todo_db.compoleted = not todo_db.compoleted
    session.add(todo_db)
    session.commit()
    session.refresh(todo_db)
    return todo_db

@app.delete("/todos/completed")
def delete_completed_todos(session: SessionDep):
    completed_todos = session.exec(select(Todo).where(Todo.compoleted == True)).all()
    deleted_count = len(completed_todos)
    for todo in completed_todos:
        session.delete(todo)
    session.commit()
    return {"ok": f"{deleted_count} completed todos deleted"}