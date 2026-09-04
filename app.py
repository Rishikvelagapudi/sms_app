import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

# ------------------------------------------------------------------
# App / Config
# ------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'student_management.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'


# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='student')  # 'admin' or 'student'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    head_of_department = db.Column(db.String(120))
    description = db.Column(db.Text)

    courses = db.relationship('Course', backref='department', lazy=True, cascade='all, delete-orphan')
    students = db.relationship('Student', backref='department', lazy=True)

    @property
    def student_count(self):
        return len(self.students)

    @property
    def course_count(self):
        return len(self.courses)


class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    credits = db.Column(db.Integer, default=3)
    duration_weeks = db.Column(db.Integer, default=16)
    description = db.Column(db.Text)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)

    registrations = db.relationship('Registration', backref='course', lazy=True, cascade='all, delete-orphan')

    @property
    def enrolled_count(self):
        return len(self.registrations)


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(30), unique=True, nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    address = db.Column(db.Text)
    enrollment_year = db.Column(db.Integer, default=lambda: datetime.utcnow().year)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=True)

    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))
    registrations = db.relationship('Registration', backref='student', lazy=True, cascade='all, delete-orphan')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Registration(db.Model):
    __tablename__ = 'registrations'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    registered_on = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Active')  # Active, Completed, Dropped

    __table_args__ = (db.UniqueConstraint('student_id', 'course_id', name='unique_student_course'),)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def admin_required(view_func):
    from functools import wraps

    @wraps(view_func)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Admin access required for that action.', 'danger')
            return redirect(url_for('home'))
        return view_func(*args, **kwargs)
    return wrapped


# ------------------------------------------------------------------
# Public Routes
# ------------------------------------------------------------------
@app.route('/')
def home():
    stats = {
        'students': Student.query.count(),
        'courses': Course.query.count(),
        'departments': Department.query.count(),
        'registrations': Registration.query.count(),
    }
    return render_template('home.html', stats=stats)


@app.route('/about')
def about():
    return render_template('about.html')


# ------------------------------------------------------------------
# Auth Routes
# ------------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    departments = Department.query.order_by(Department.name).all()

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        department_id = request.form.get('department_id')

        errors = []
        if not username or not email or not password:
            errors.append('Username, email and password are required.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if User.query.filter_by(username=username).first():
            errors.append('Username already taken.')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('register.html', departments=departments, form=request.form)

        user = User(username=username, email=email, role='student')
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # get user.id before commit

        if first_name and last_name and department_id:
            roll_number = f"STU{datetime.utcnow().year}{User.query.count():04d}"
            student = Student(
                roll_number=roll_number,
                first_name=first_name,
                last_name=last_name,
                email=email,
                department_id=department_id,
                user_id=user.id
            )
            db.session.add(student)

        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', departments=departments, form={})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


# ------------------------------------------------------------------
# Department Routes
# ------------------------------------------------------------------
@app.route('/departments')
def departments():
    all_departments = Department.query.order_by(Department.name).all()
    return render_template('departments.html', departments=all_departments)


@app.route('/departments/add', methods=['GET', 'POST'])
@admin_required
def add_department():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip().upper()
        head = request.form.get('head_of_department', '').strip()
        description = request.form.get('description', '').strip()

        if not name or not code:
            flash('Name and code are required.', 'danger')
            return render_template('department_form.html', form=request.form)

        if Department.query.filter((Department.name == name) | (Department.code == code)).first():
            flash('A department with that name or code already exists.', 'danger')
            return render_template('department_form.html', form=request.form)

        dept = Department(name=name, code=code, head_of_department=head, description=description)
        db.session.add(dept)
        db.session.commit()
        flash('Department added successfully.', 'success')
        return redirect(url_for('departments'))

    return render_template('department_form.html', form={})


@app.route('/departments/<int:dept_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    if request.method == 'POST':
        dept.name = request.form.get('name', '').strip()
        dept.code = request.form.get('code', '').strip().upper()
        dept.head_of_department = request.form.get('head_of_department', '').strip()
        dept.description = request.form.get('description', '').strip()
        db.session.commit()
        flash('Department updated successfully.', 'success')
        return redirect(url_for('departments'))
    return render_template('department_form.html', form=dept, editing=True)


@app.route('/departments/<int:dept_id>/delete', methods=['POST'])
@admin_required
def delete_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    db.session.delete(dept)
    db.session.commit()
    flash('Department deleted.', 'info')
    return redirect(url_for('departments'))


# ------------------------------------------------------------------
# Course Routes
# ------------------------------------------------------------------
@app.route('/courses')
def courses():
    all_courses = Course.query.order_by(Course.name).all()
    return render_template('courses.html', courses=all_courses)


@app.route('/courses/<int:course_id>')
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    is_registered = False
    if current_user.is_authenticated and current_user.student_profile:
        is_registered = Registration.query.filter_by(
            student_id=current_user.student_profile.id, course_id=course.id
        ).first() is not None
    return render_template('course_detail.html', course=course, is_registered=is_registered)


@app.route('/courses/add', methods=['GET', 'POST'])
@admin_required
def add_course():
    departments_list = Department.query.order_by(Department.name).all()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip().upper()
        credits = request.form.get('credits', 3)
        duration_weeks = request.form.get('duration_weeks', 16)
        description = request.form.get('description', '').strip()
        department_id = request.form.get('department_id')

        if not name or not code or not department_id:
            flash('Name, code and department are required.', 'danger')
            return render_template('course_form.html', departments=departments_list, form=request.form)

        if Course.query.filter_by(code=code).first():
            flash('A course with that code already exists.', 'danger')
            return render_template('course_form.html', departments=departments_list, form=request.form)

        course = Course(
            name=name, code=code, credits=credits, duration_weeks=duration_weeks,
            description=description, department_id=department_id
        )
        db.session.add(course)
        db.session.commit()
        flash('Course added successfully.', 'success')
        return redirect(url_for('courses'))

    return render_template('course_form.html', departments=departments_list, form={})


@app.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    departments_list = Department.query.order_by(Department.name).all()
    if request.method == 'POST':
        course.name = request.form.get('name', '').strip()
        course.code = request.form.get('code', '').strip().upper()
        course.credits = request.form.get('credits', 3)
        course.duration_weeks = request.form.get('duration_weeks', 16)
        course.description = request.form.get('description', '').strip()
        course.department_id = request.form.get('department_id')
        db.session.commit()
        flash('Course updated successfully.', 'success')
        return redirect(url_for('courses'))
    return render_template('course_form.html', departments=departments_list, form=course, editing=True)


@app.route('/courses/<int:course_id>/delete', methods=['POST'])
@admin_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted.', 'info')
    return redirect(url_for('courses'))


@app.route('/courses/<int:course_id>/register', methods=['POST'])
@login_required
def register_course(course_id):
    course = Course.query.get_or_404(course_id)
    student = current_user.student_profile

    if not student:
        flash('Only students with a linked profile can register for courses.', 'danger')
        return redirect(url_for('course_detail', course_id=course_id))

    existing = Registration.query.filter_by(student_id=student.id, course_id=course.id).first()
    if existing:
        flash('You are already registered for this course.', 'warning')
    else:
        reg = Registration(student_id=student.id, course_id=course.id)
        db.session.add(reg)
        db.session.commit()
        flash(f'Successfully registered for {course.name}!', 'success')

    return redirect(url_for('course_detail', course_id=course_id))


@app.route('/courses/<int:course_id>/unregister', methods=['POST'])
@login_required
def unregister_course(course_id):
    student = current_user.student_profile
    if student:
        reg = Registration.query.filter_by(student_id=student.id, course_id=course_id).first()
        if reg:
            db.session.delete(reg)
            db.session.commit()
            flash('You have unregistered from the course.', 'info')
    return redirect(url_for('course_detail', course_id=course_id))


@app.route('/my-courses')
@login_required
def my_courses():
    student = current_user.student_profile
    if not student:
        flash('No student profile linked to this account.', 'warning')
        return redirect(url_for('home'))
    return render_template('my_courses.html', student=student)


# ------------------------------------------------------------------
# Student Routes
# ------------------------------------------------------------------
@app.route('/students')
@login_required
def students():
    all_students = Student.query.order_by(Student.first_name).all()
    return render_template('students.html', students=all_students)


@app.route('/students/<int:student_id>')
@login_required
def student_detail(student_id):
    student = Student.query.get_or_404(student_id)
    return render_template('student_detail.html', student=student)


@app.route('/students/add', methods=['GET', 'POST'])
@admin_required
def add_student():
    departments_list = Department.query.order_by(Department.name).all()
    if request.method == 'POST':
        roll_number = request.form.get('roll_number', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        gender = request.form.get('gender', '')
        address = request.form.get('address', '').strip()
        department_id = request.form.get('department_id')
        enrollment_year = request.form.get('enrollment_year') or datetime.utcnow().year

        if not roll_number or not first_name or not last_name or not email or not department_id:
            flash('Roll number, name, email and department are required.', 'danger')
            return render_template('student_form.html', departments=departments_list, form=request.form)

        if Student.query.filter((Student.roll_number == roll_number) | (Student.email == email)).first():
            flash('A student with that roll number or email already exists.', 'danger')
            return render_template('student_form.html', departments=departments_list, form=request.form)

        student = Student(
            roll_number=roll_number, first_name=first_name, last_name=last_name,
            email=email, phone=phone, gender=gender, address=address,
            department_id=department_id, enrollment_year=enrollment_year
        )
        db.session.add(student)
        db.session.commit()
        flash('Student added successfully.', 'success')
        return redirect(url_for('students'))

    return render_template('student_form.html', departments=departments_list, form={})


@app.route('/students/<int:student_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    departments_list = Department.query.order_by(Department.name).all()
    if request.method == 'POST':
        student.roll_number = request.form.get('roll_number', '').strip()
        student.first_name = request.form.get('first_name', '').strip()
        student.last_name = request.form.get('last_name', '').strip()
        student.email = request.form.get('email', '').strip()
        student.phone = request.form.get('phone', '').strip()
        student.gender = request.form.get('gender', '')
        student.address = request.form.get('address', '').strip()
        student.department_id = request.form.get('department_id')
        student.enrollment_year = request.form.get('enrollment_year') or student.enrollment_year
        db.session.commit()
        flash('Student updated successfully.', 'success')
        return redirect(url_for('students'))
    return render_template('student_form.html', departments=departments_list, form=student, editing=True)


@app.route('/students/<int:student_id>/delete', methods=['POST'])
@admin_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted.', 'info')
    return redirect(url_for('students'))


# ------------------------------------------------------------------
# Contact
# ------------------------------------------------------------------
@app.route('/contact', methods=['POST'])
def contact():
    name = request.form.get('name', '').strip()
    flash(f'Thanks {name}, your message has been received. We will get back to you soon.', 'success')
    return redirect(url_for('about'))


# ------------------------------------------------------------------
# Error Handlers
# ------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


# ------------------------------------------------------------------
# CLI: init-db
# ------------------------------------------------------------------
@app.cli.command('init-db')
def init_db():
    """Create tables and seed an admin user + sample data."""
    db.create_all()

    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@campus.edu', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

    if Department.query.count() == 0:
        cse = Department(name='Computer Science & Engineering', code='CSE',
                          head_of_department='Dr. A. Rao', description='Focuses on software, AI and systems.')
        ece = Department(name='Electronics & Communication', code='ECE',
                          head_of_department='Dr. S. Kumar', description='Focuses on electronics and communication systems.')
        mech = Department(name='Mechanical Engineering', code='MECH',
                           head_of_department='Dr. P. Sharma', description='Focuses on mechanical design and manufacturing.')
        db.session.add_all([cse, ece, mech])
        db.session.flush()

        db.session.add_all([
            Course(name='Data Structures & Algorithms', code='CSE201', credits=4, duration_weeks=16,
                   description='Core data structures, algorithms and complexity analysis.', department_id=cse.id),
            Course(name='Machine Learning', code='CSE305', credits=4, duration_weeks=16,
                   description='Supervised, unsupervised learning and neural networks.', department_id=cse.id),
            Course(name='Digital Signal Processing', code='ECE210', credits=3, duration_weeks=14,
                   description='Signal analysis and processing techniques.', department_id=ece.id),
            Course(name='Thermodynamics', code='MECH150', credits=3, duration_weeks=14,
                   description='Laws of thermodynamics and heat transfer.', department_id=mech.id),
        ])

    db.session.commit()
    print('Database initialized with admin user (admin / admin123) and sample data.')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
