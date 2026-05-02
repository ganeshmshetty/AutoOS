import os
from sqlmodel import SQLModel, create_engine, Session

# Set up SQLite database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///workflows.db")
engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    from models.workflow import Workflow
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
