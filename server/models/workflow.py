from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON
from datetime import datetime, timezone
import uuid

class Workflow(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    description: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    events: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    source: str = Field(default="extension") # "extension" or "chat"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
