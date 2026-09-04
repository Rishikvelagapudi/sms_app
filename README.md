# DR RVR NRI Institution of Technology — Student Management System

A full-stack Student Management System built with **Django**, **SQLite3**, and **Bootstrap 5**.

## Features

- **Home** — dashboard with live stats (students, courses, departments, registrations, attendance logs, active elections)
- **Students** — list, view, add, edit, delete student records (admin manages; any logged-in user can view)
- **Courses** — browse catalog, view details, **self-register/unregister** for courses
- **Departments** — list, add, edit, delete departments with head & description
- **Attendance System**:
  - **Admin**: Mark roll call by course and date with 1-click *"Mark All Present"* / *"Mark All Absent"*, record remarks, and view full course-level percentage reports.
  - **Students**: Dedicated *"My Attendance"* dashboard with overall percentage progress bar, course-by-course attendance rates, recent class session logs, and automatic 75% eligibility shortage alerts.
- **Voting System (Campus Elections)**:
  - **Admin**: Create and schedule elections, configure positions (*President, General Secretary, etc.*), register candidates with manifestos and symbols, and toggle active status.
  - **Students**: Cast secure single-choice digital ballots per position with protection against double-voting, and inspect real-time/concluded election results with visual percentage bars and winner badges.
- **About / Contact** — info page with a working contact form
- **Auth** — Register (creates account + optional linked student profile), Login, Logout
- **Roles** — `admin` (full CRUD access + Django Admin panel) and `student` (view, attendance tracking, self-registration, and campus voting)
- **My Courses** — logged-in students see their own registrations
- **Django Admin** — rich admin dashboard at `/admin/`

## Tech Stack

| Layer      | Technology              |
|------------|--------------------------|
| Backend    | Django 5/6, Django Auth, Django ORM |
| Database   | SQLite3                 |
| Frontend   | Django Templates + Bootstrap 5 + Bootstrap Icons |
| Auth       | Django built-in PBKDF2 password hashing & session authentication |

## Project Structure

```
student_management/
├── manage.py
├── requirements.txt
├── instance/
│   └── db.sqlite3           # SQLite database
├── sms_project/             # Project configuration
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── core/                    # Main app
│   ├── models.py            # User, Department, Course, Student, Registration, Attendance, Election, Candidate, Vote
│   ├── views.py             # View functions and business logic
│   ├── urls.py              # URL mappings
│   ├── admin.py             # Django admin registrations
│   ├── tests.py             # Unit tests for attendance & voting
│   └── management/commands/
│       └── init_db.py       # DB seed command with sample attendance & elections
├── static/
│   └── css/style.css        # Custom orange theme styling
└── templates/
    ├── base.html            # Navbar, messages, footer
    ├── home.html
    ├── students.html / student_form.html / student_detail.html
    ├── courses.html / course_form.html / course_detail.html / my_courses.html
    ├── departments.html / department_form.html
    ├── attendance_dashboard.html / mark_attendance.html / course_attendance_report.html / my_attendance.html
    ├── elections_list.html / election_ballot.html / election_results.html / admin_elections.html / admin_election_form.html
    ├── about.html
    ├── login.html / register.html
    └── 404.html
```

## Setup & Run

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Apply migrations**
   ```bash
   python manage.py migrate
   ```

3. **Initialize the database** (creates admin user, sample students, attendance logs & sample election)
   ```bash
   python manage.py init_db
   ```

4. **Run tests**
   ```bash
   python manage.py test core
   ```

5. **Run the server**
   ```bash
   python manage.py runserver 5000
   ```
   Visit **http://127.0.0.1:5000** (or Django Admin at **http://127.0.0.1:5000/admin/**)

## Default Test Logins

| Username | Password   | Role    | Access Description |
|----------|------------|---------|-------------------|
| `admin`  | `admin123` | Admin   | Full management, mark attendance, manage elections, Django Admin `/admin/` |
| `rahul`  | `student123`| Student| View attendance, register courses, vote in campus elections |
| `priya`  | `student123`| Student| View attendance, register courses, vote in campus elections |


