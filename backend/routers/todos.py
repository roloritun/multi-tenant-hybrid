from fastapi import APIRouter, Request, Depends
from typing import List
from schemas.todo import TodoCreate, Todo
from services.todo_service import todo_service
from services.monitoring import metrics
from security.auth import get_current_user
from models.user import User

router = APIRouter()

@router.get("/todos", response_model=List[Todo])
@metrics.track_request()
async def list_todos(request: Request, current_user: User = Depends(get_current_user)):
    """List todos for the current tenant"""
    return todo_service.get_todos(request.state.db, request.state.tenant_id)

@router.post("/todos", response_model=Todo)
@metrics.track_request()
async def create_todo(request: Request, todo: TodoCreate, current_user: User = Depends(get_current_user)):
    """Create a new todo"""
    return todo_service.create_todo(
        request.state.db,
        todo,
        request.state.tenant_id,
        current_user.id
    )

@router.put("/todos/{todo_id}", response_model=Todo)
@metrics.track_request()
async def update_todo(todo_id: int, todo: TodoCreate, request: Request, current_user: User = Depends(get_current_user)):
    """Update a todo"""
    return todo_service.update_todo(
        request.state.db,
        todo_id,
        todo,
        request.state.tenant_id
    )

@router.delete("/todos/{todo_id}")
@metrics.track_request()
async def delete_todo(todo_id: int, request: Request, current_user: User = Depends(get_current_user)):
    """Delete a todo"""
    todo_service.delete_todo(request.state.db, todo_id, request.state.tenant_id)
    return {"message": "Todo deleted"} 