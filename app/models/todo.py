from sqlmodel import Field, SQLModel


class TodoBase(SQLModel):
    title: str = Field(..., min_length=1, max_length=10)


class Todo(TodoBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    compoleted: bool = Field(default=False)


class TodoCreate(TodoBase):
    pass
