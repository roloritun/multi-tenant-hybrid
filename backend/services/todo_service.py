from sqlalchemy.orm import Session
from typing import List, Optional
from models.todo import Todo
from schemas.todo import TodoCreate
from fastapi import HTTPException
from config.tenant_config import config_manager
import logging

logger = logging.getLogger(__name__)

class TodoService:
    @staticmethod
    def get_todos(db: Session, tenant_id: int) -> List[Todo]:
        """Get all todos for a tenant"""
        return db.query(Todo).filter_by(tenant_id=tenant_id).all()
    
    @staticmethod
    def get_todo(db: Session, todo_id: int, tenant_id: int) -> Optional[Todo]:
        """Get a specific todo"""
        todo = db.query(Todo).filter_by(
            id=todo_id,
            tenant_id=tenant_id
        ).first()
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        return todo
    
    @staticmethod
    def create_todo(db: Session, todo_data: TodoCreate, tenant_id: int, user_id: int) -> Todo:
        """Create a new todo"""
        try:
            # Check quota
            current_todos = db.query(Todo).filter_by(tenant_id=tenant_id).count()
            tenant_config = config_manager.get_tenant_config(tenant_id)
            max_todos = tenant_config['quotas'].get('max_todos', 1000)
            
            if current_todos >= max_todos:
                raise HTTPException(status_code=429, detail="Todo limit reached")
            
            new_todo = Todo(
                **todo_data.dict(),
                tenant_id=tenant_id,
                created_by=user_id
            )
            
            db.add(new_todo)
            db.commit()
            db.refresh(new_todo)
            
            return new_todo
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating todo: {str(e)}")
            raise
    
    @staticmethod
    def update_todo(db: Session, todo_id: int, todo_data: TodoCreate, tenant_id: int) -> Todo:
        """Update a todo"""
        try:
            todo = TodoService.get_todo(db, todo_id, tenant_id)
            
            for key, value in todo_data.dict().items():
                setattr(todo, key, value)
            
            db.commit()
            db.refresh(todo)
            return todo
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating todo: {str(e)}")
            raise
    
    @staticmethod
    def delete_todo(db: Session, todo_id: int, tenant_id: int) -> None:
        """Delete a todo"""
        try:
            todo = TodoService.get_todo(db, todo_id, tenant_id)
            db.delete(todo)
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting todo: {str(e)}")
            raise

todo_service = TodoService() 