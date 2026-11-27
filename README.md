# Project 20 — Agentic Triage Assistant (Student + Admin Panels)

## Run on Windows
1. Open this folder in VS Code.
2. Open Terminal (PowerShell) in this folder.
3. Create and activate a virtual environment:

```powershell
py -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

4. Install dependencies:

```powershell
pip install -r requirements.txt
```

5. Start the server:

```powershell
python -m uvicorn app.main:app --reload
```

6. Open http://127.0.0.1:8000

## Student access
Use **Student Register** to create a student account, then log in. Students can submit complaints and see only their own complaints.

## Admin access (demo credentials)
- Username: `admin`
- Password: `Admin@12345`

The admin account is created automatically on first startup if it does not already exist. For a real deployment, set `ADMIN_USERNAME` and `ADMIN_PASSWORD` environment variables before starting the server and use a strong secret key; the included credentials are for local demonstration only.

## Panels
- Student dashboard: submit complaints and track status.
- Admin dashboard: view all complaints, filter by status, assign a department, and update status.
- Backend endpoints enforce student/admin access separately.

The original triage rules and deduplicator module are retained. This is a student demonstration project, not a production campus security system.


## Compatibility note
This edition uses lightweight text similarity for duplicate detection. It does not require FAISS, NumPy, or Sentence Transformers, avoiding their platform/Python-version wheel issues.
