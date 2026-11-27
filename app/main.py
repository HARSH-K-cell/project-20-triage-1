import os
import random
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import init_db, get_db, User, Ticket, SessionLocal
from app.auth import hash_password, verify_password, create_access_token, decode_token
from app.triage_agent import triage_complaint
from app.deduplicator import deduplicator

app = FastAPI(title="Project 20: Agentic Triage Assistant")
init_db()

def ensure_admin():
    db = SessionLocal()
    try:
        username = os.getenv("ADMIN_USERNAME", "admin")
        password = os.getenv("ADMIN_PASSWORD", "Admin@12345")
        admin = db.query(User).filter(User.username == username).first()
        if not admin:
            db.add(User(username=username, email=f"{username}@eastpoint.edu.in",
                        hashed_password=hash_password(password), role="admin"))
            db.commit()
    finally:
        db.close()

ensure_admin()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("static/index.html")

class RegisterSchema(BaseModel):
    username: str
    email: str
    password: str

class LoginSchema(BaseModel):
    username: str
    password: str

class TicketSubmitSchema(BaseModel):
    student_name: str
    content: str

class TicketUpdateSchema(BaseModel):
    status: str
    assigned_department: Optional[str] = None

def current_user(authorization: Optional[str] = Header(default=None),
                 db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Please log in")
    payload = decode_token(authorization.split(" ", 1)[1])
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid or expired login")
    user = db.query(User).filter(User.username == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="Account not found")
    return user

def admin_only(user: User = Depends(current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")
    return user

@app.post("/api/auth/register")
def register(data: RegisterSchema, db: Session = Depends(get_db)):
    username = data.username.strip()
    email = data.email.strip().lower()
    if not username or len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Username is required and password must be at least 6 characters")
    if db.query(User).filter((User.username == username) | (User.email == email)).first():
        raise HTTPException(status_code=400, detail="Username or email already exists")
    user = User(username=username, email=email, hashed_password=hash_password(data.password), role="student")
    db.add(user)
    db.commit()
    return {"message": "Student account created. You can now log in."}

@app.post("/api/auth/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username.strip()).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": token, "role": user.role, "username": user.username}

@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return {"username": user.username, "role": user.role}

@app.post("/api/tickets/submit")
def submit_ticket(data: TicketSubmitSchema, user: User = Depends(current_user),
                  db: Session = Depends(get_db)):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only student accounts can submit complaints")
    triage = triage_complaint(data.content)
    ticket_code = f"TICK-{random.randint(1000, 9999)}"
    ticket = Ticket(
        ticket_code=ticket_code,
        student_name=data.student_name.strip() or user.username,
        submitted_by=user.username,
        content=data.content.strip(),
        category=triage["category"],
        urgency=triage["urgency"],
        is_emergency=triage["is_emergency"],
        status="CRITICAL BYPASS" if triage["is_emergency"] else "Open",
        assigned_department=triage.get("routed_to")
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return {
        "status": "EMERGENCY_BYPASS" if triage["is_emergency"] else "CREATED",
        "message": "Emergency safety bypass triggered. Contact campus security immediately." if triage["is_emergency"] else "Complaint triaged and submitted successfully.",
        "ticket": {"ticket_code": ticket.ticket_code, "category": ticket.category,
                   "urgency": ticket.urgency, "status": ticket.status,
                   "assigned_department": ticket.assigned_department}
    }

def ticket_dict(t):
    return {
        "id": t.id, "ticket_code": t.ticket_code, "student_name": t.student_name,
        "submitted_by": t.submitted_by, "content": t.content, "category": t.category,
        "urgency": t.urgency, "status": t.status, "assigned_department": t.assigned_department,
        "is_emergency": bool(t.is_emergency), "merged_count": t.merged_count,
        "created_at": t.created_at.isoformat() if t.created_at else None
    }

@app.get("/api/tickets/mine")
def my_tickets(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [ticket_dict(t) for t in db.query(Ticket).filter(Ticket.submitted_by == user.username)
            .order_by(Ticket.id.desc()).all()]

@app.get("/api/admin/tickets")
def all_tickets(user: User = Depends(admin_only), db: Session = Depends(get_db)):
    return [ticket_dict(t) for t in db.query(Ticket).order_by(Ticket.id.desc()).all()]

@app.get("/api/admin/stats")
def admin_stats(user: User = Depends(admin_only), db: Session = Depends(get_db)):
    tickets = db.query(Ticket).all()
    return {
        "total": len(tickets),
        "open": sum(1 for t in tickets if t.status.lower() == "open"),
        "critical": sum(1 for t in tickets if t.is_emergency or t.urgency.upper() == "CRITICAL"),
        "resolved": sum(1 for t in tickets if t.status.lower() == "resolved")
    }

@app.patch("/api/admin/tickets/{ticket_id}")
def update_ticket(ticket_id: int, data: TicketUpdateSchema,
                  user: User = Depends(admin_only), db: Session = Depends(get_db)):
    allowed = {"Open", "In Progress", "Resolved", "Rejected"}
    if data.status not in allowed:
        raise HTTPException(status_code=400, detail="Invalid status")
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = data.status
    if data.assigned_department is not None:
        ticket.assigned_department = data.assigned_department
    db.commit()
    db.refresh(ticket)
    return ticket_dict(ticket)
