# Task App

A Flask task management application I built to practice full-stack development and deployment. Users can create an account, organize their tasks, and manage their daily agenda.

**Live demo:** https://tasks.johnnyhceleste.com

## Features

- User registration and login
- Create, edit, and delete tasks with confirmation
- Mark tasks complete using a checkbox
- Separate Active, Today, Upcoming, Completed, and All views
- Drag-and-drop ordering in the Active view
- Search task titles and filter by priority or category
- Sort by due date, priority, or creation order
- Optional task descriptions and due dates
- Visual indicators for overdue tasks
- Toast messages for feedback
- Save an email address and notification preferences

## Technology

- Python and Flask
- Flask-Login and Flask-WTF
- SQLAlchemy and SQLite
- HTML, CSS, JavaScript, and Jinja templates
- AWS EC2 running Ubuntu
- Gunicorn, systemd, and Caddy for hosting and HTTPS

## Run Locally

The following commands use Windows PowerShell.

### 1. Clone the repository

```powershell
git clone https://github.com/johnnyboyceleste23/Task-App.git
cd Task-App
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Set a local secret key

```powershell
$env:SECRET_KEY = (python -c "import secrets; print(secrets.token_hex(32))")
```

The key is available in the current terminal session. Keep it out of source code and version control.

### 5. Start the application

```powershell
python app.py
```

On a fresh setup, this creates the database tables in `instance/database.db`.

Open http://127.0.0.1:5000 in your browser and create an account.

## Deployment

The live application runs on AWS EC2. Gunicorn serves the Flask application, systemd manages the application service, and Caddy provides HTTPS and forwards requests to Gunicorn.

Updates are pushed to GitHub and pulled onto the server. Database model changes require a separate migration; `db.create_all()` does not update existing tables.

## Email Notifications — In Progress

Users can save an email address and enable or disable reminder preferences. Actual email delivery is not implemented yet.

When running locally with `python app.py`, the current background job prints potential reminders to the terminal. This job does not start through the deployed Gunicorn service.

## Author

Johnny Celeste