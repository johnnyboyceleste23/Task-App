from sqlite3 import Date
import os
from flask import Flask, render_template, url_for, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from datetime import date
from datetime import date as calendar_date
from sqlalchemy import case
from flask_toastr import Toastr
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Blueprint
from flask_login import current_user
import threading
from sqlalchemy.exc import IntegrityError
import os
import resend
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'



csrf = CSRFProtect(app)

toastr = Toastr(app)

app.config["TOASTR_TIMEOUT"] = 3000
app.config["TOASTR_EXTENDED_TIMEOUT"] = 1000

app.config["TOASTR_PROGRESS_BAR"] = True
load_dotenv()
resend.api_key = os.environ.get("RESEND_API_KEY")
db = SQLAlchemy(app)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=True)
    email_notification = db.Column(db.Boolean, default=False, nullable=True)
    last_reminder = db.Column(db.DateTime, nullable=True)




class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    is_complete = db.Column(db.Boolean, default=False, nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, nullable=True)
    priority = db.Column(db.Text, nullable=False)
    category = db.Column(db.Text, nullable=True)
    position = db.Column(db.Integer, nullable=False)




@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route('/')

def home():
    return render_template("index.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email', '').strip()




        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('signup'))
        if not username or not password:
            flash('Please enter all fields')
            return redirect(url_for('signup'))
        if username.strip() == '' or password.strip() == '':
            flash('Please enter all fields')
            return redirect(url_for('signup'))

        user = User(
            username=username,
            password=generate_password_hash(password),
            email=email or None,

        )
        db.session.add(user)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("That username or email address is already in use.", "danger")
            return redirect(url_for("signup"))
        return redirect(url_for('home'))
    return render_template("signup.html")

@app.route('/email_notification', methods=['GET', 'POST'])
@login_required
def email_notification():
    if request.method == 'POST':
        wants_reminders = "email_notification" in request.form
        email_submission = request.form.get('email', "").strip()

        if wants_reminders and not current_user.email:
            if not email_submission:
                flash("Please enter an email address", "danger")
                return redirect(url_for('dashboard'))
            current_user.email = email_submission
        current_user.email_notification = wants_reminders
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("That email address is already in use.", "danger")

    return redirect(url_for('dashboard'))





@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    tasks = Task.query.filter_by(user_id=current_user.id, is_deleted=False, is_complete=False).all()



    view = request.args.get('view', 'active')
    sort = request.args.get('sort', 'due_date')
    filter_category = request.args.get('sort_category', 'all')
    print(current_user.email)
    if request.method == 'GET':
        search = request.args.get('search', '')
        priority = request.args.get('priority', '')



    elif request.method == 'POST':
        title = request.form.get('title')
        date_text = request.form.get('due_date')
        description = request.form.get('description')
        priority = request.form.get('priority')
        category = request.form.get('category')





        if not category:
            category = None

        if not priority:
            flash("Enter a priority", "danger")
            return redirect(url_for('dashboard'))
        if date_text:
            due_date = datetime.strptime(date_text, '%Y-%m-%d').date()


        else:
            due_date = None
        if not description:
            description = None
        if not title or title.strip() == '':
            flash("Enter a task", "danger")
            return redirect(url_for('dashboard'))


        last_position = db.session.query(
            db.func.max(Task.position)
        ).filter(Task.user_id == current_user.id).scalar()
        new_position = (last_position or 0) + 1
        task = Task(title=title, due_date=due_date, description=description, priority=priority, category=category, user_id=current_user.id, is_deleted=False, is_complete=False, position=new_position)
        db.session.add(task)
        db.session.commit()



        return redirect(url_for('dashboard'))

    priority_order = case(
        (Task.priority == 'high', 1),
        (Task.priority == 'medium', 2),
        (Task.priority == 'low', 3),
        else_=4
    )

    query = Task.query.filter_by(
        user_id=current_user.id,
        is_deleted=False,
    )

    if view == "completed":
        query = query.filter_by(is_complete=True)
        print(current_user.email)
    elif view == "today":
        query = query.filter_by(
            is_complete=False,
            due_date=calendar_date.today(),
        )
    elif view == "upcoming":
        query = query.filter_by(is_complete=False).filter(
            Task.due_date > calendar_date.today()
        )
    elif view == "search_tasks":
        query = query.filter_by(is_complete=False)
    elif view == "active":
        query = query.filter_by(is_complete=False)
        sort = "manual_order"
        if tasks:
            flash("Hold Click and Drag To Move Cards", "info")


    if view == "search_tasks":
        #These decides which tasks show up
        if search:
            query = query.filter(Task.title.contains(search))
        if priority and priority != "all": #If user entered a priority only filter that one
            query = query.filter(Task.priority == priority)
        if filter_category and filter_category != "all":
            query = query.filter(Task.category == filter_category)




    if sort == "priority":
        query = query.order_by(priority_order, Task.position, Task.id)
    elif sort == "due_date":
        query = query.order_by(
            Task.due_date.is_(None),
            Task.due_date.asc(),
            Task.id,
        )
    elif sort == "manual_order":
        query = query.order_by(Task.position, Task.id)
    else:
        query = query.order_by(Task.id.asc())

    tasks = query.all()


    return render_template('dashboard.html', user=current_user, tasks=tasks, today=calendar_date.today(), view=view, sort=sort)



@app.route('/soft_delete_task/<int:current_id>', methods=['POST'])
@login_required
def soft_delete_task(current_id):
    check = db.session.get(Task, current_id)

    if check:
        print(check.id, check.user_id, check.is_deleted, check.is_complete)
    else:
        print("Task does not exist")
    task = Task.query.filter_by(id=current_id, user_id=current_user.id, is_deleted=False, is_complete=False).first_or_404()
    task.is_deleted = True
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id, is_deleted=False, is_complete=False).first_or_404()
    if request.method == 'GET':
        return render_template('edit.html', task=task)

    elif request.method == 'POST':
        title = request.form.get('title')
        date_text = request.form.get('due_date')
        description = request.form.get('description')
        priority = request.form.get('priority')
        category = request.form.get('category')
        if not category:
            category = None
        if not priority:
            flash("Enter a priority", "danger")
            return redirect(url_for('dashboard'))
        if date_text:
            due_date = datetime.strptime(date_text, '%Y-%m-%d').date()
        else:
            due_date = None
        if not description:
            description = None
        if not title:
            flash("Enter a task", "danger")
            return redirect(url_for('dashboard'))
        if title.strip() == '':
            flash("Enter a task", "danger")
            return redirect(url_for('dashboard'))
        task.title = title
        task.due_date = due_date
        task.description = description
        task.priority = priority
        task.category = category
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('dashboard.html', user=current_user, task=task)
@app.route('/complete/<int:task_id>', methods=['POST'])
@login_required
def complete(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id, is_deleted=False).first_or_404()
    task.is_complete = True
    db.session.commit()
    if task.is_complete:
        flash("Task completed", "success")

    return redirect(url_for('dashboard'))

@app.route('/tasks/reorder', methods=['POST'])
@login_required
def reorder_tasks():

    data = request.get_json()

    order_ids = data.get('ordered_ids') if isinstance(data, dict) else None

    if not isinstance(order_ids, list):
        return {"error": "Expected a list of task IDs."}, 400

    for task_id in order_ids:
        if type(task_id) is not int:
            return {"error": "Each task ID must be an integer."}, 400

        active_task = Task.query.filter_by(user_id=current_user.id, is_complete=False, is_deleted=False).all()
        active_ids = [task.id for task in active_task]

        if len(order_ids) != len(active_ids) or set(order_ids) != set(active_ids):
            return {"error": "Your task list changed. Refresh and try again."}, 409

    for position, task_id in enumerate(order_ids, start=1):
        task = Task.query.filter_by(id=task_id, user_id=current_user.id, is_complete=False, is_deleted=False).first_or_404()
        task.position = position
        db.session.commit()

    return {"ok": True}




@app.route('/notification_center', methods=['GET'])
@login_required
def notification_center():
    tasks = Task.query.filter_by(user_id=current_user.id, is_deleted=False, is_complete=False).all()

    return render_template('notification.html', user=current_user, tasks=tasks, today=calendar_date.today(), due_date=Task.due_date)

def my_background_task():
    with app.app_context():
        today = datetime.now(ZoneInfo("America/New_York")).date()
        users = User.query.filter_by(email_notification=True).all()

        for user in users:
            if not user.email or user.last_reminder == today:
                continue

            due_tasks = Task.query.filter_by(
                user_id=user.id,
                is_deleted=False,
                is_complete=False,
                due_date=today
            ).all()


            if user.last_reminder == today:
                continue
            try:
                resend.Emails.send({
                    "from": "Task App <reminders@mail.johnnyhceleste.com>",
                    "to": [user.email],
                    "subject": "Your tasks due today",
                    "html": render_template(
                        "email_tasks.html",
                        user=user,
                        due_tasks=due_tasks
                    ),
                })
                user.last_reminder = today
                db.session.commit()
                print(f"Reminder submitted for user {user.id}")

            except Exception:
                db.session.rollback()
                app.logger.exception(
                    "Reminder failed for user %s", user.id
                )


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("create_all ran. Database file:", db.engine.url.database)


    scheduler = BackgroundScheduler(timezone="America/New_York")
    scheduler.add_job(
        my_background_task,
        trigger="cron",
        hour=8,
        minute=0
    )
    scheduler.start()
    atexit.register(scheduler.shutdown)

    app.run(debug=False, use_reloader=False)

