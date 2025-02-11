from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TodoBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None

class TodoCreate(TodoBase):
    pass

class Todo(TodoBase):
    id: int
    tenant_id: int
    created_by: int
    completed: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True 