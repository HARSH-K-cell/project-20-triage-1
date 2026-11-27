import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./project20.db")
connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
engine = create_engine(DB_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="student")

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    ticket_code = Column(String, unique=True, index=True)
    student_name = Column(String, nullable=False)
    submitted_by = Column(String, nullable=True, index=True)
    content = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    urgency = Column(String, nullable=False)
    status = Column(String, default="Open")
    assigned_department = Column(String, nullable=True)
    is_emergency = Column(Boolean, default=False)
    merged_count = Column(Integer, default=1)
    master_ticket_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
    # Lightweight migration for databases created by the earlier version.
    if DB_URL.startswith("sqlite"):
        from sqlalchemy import inspect, text
        columns = {c["name"] for c in inspect(engine).get_columns("tickets")}
        with engine.begin() as conn:
            if "submitted_by" not in columns:
                conn.execute(text("ALTER TABLE tickets ADD COLUMN submitted_by VARCHAR"))
            if "assigned_department" not in columns:
                conn.execute(text("ALTER TABLE tickets ADD COLUMN assigned_department VARCHAR"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
