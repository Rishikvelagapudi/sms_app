import os
from datetime import datetime, date, timedelta
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q
from django.conf import settings
from .models import (
    User, Department, Course, Student, Registration,
    Attendance, Election, ElectionPosition, Candidate, Vote
)


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to access this page.')
            return redirect(f"{reverse('login')}?next={request.path}")
        if getattr(request.user, 'role', '') != 'admin' and not request.user.is_staff and not request.user.is_superuser:
            messages.error(request, 'Admin access required for that action.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapped


# ------------------------------------------------------------------
# Public Views
# ------------------------------------------------------------------
def home(request):
    stats = {
        'students': Student.objects.count(),
        'courses': Course.objects.count(),
        'departments': Department.objects.count(),
        'registrations': Registration.objects.count(),
        'active_elections': Election.objects.filter(is_active=True).count(),
        'total_attendances': Attendance.objects.count(),
    }
    return render(request, 'home.html', {'stats': stats})


def readme_view(request):
    readme_content = ""
    readme_path = os.path.join(settings.BASE_DIR, 'README.md')
    try:
        if os.path.exists(readme_path):
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
    except Exception:
        readme_content = "# README\n\nUnable to load README.md."

    return render(request, 'readme.html', {
        'readme_content': readme_content,
    })


def about(request):
    return render(request, 'about.html')


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        messages.success(request, f'Thanks {name}, your message has been received. We will get back to you soon.')
    return redirect('about')


# ------------------------------------------------------------------
# Auth Views
# ------------------------------------------------------------------
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    departments_list = Department.objects.order_by('name')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        department_id = request.POST.get('department_id')

        errors = []
        if not username or not email or not password:
            errors.append('Username, email and password are required.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if User.objects.filter(username=username).exists():
            errors.append('Username already taken.')
        if User.objects.filter(email=email).exists():
            errors.append('Email already registered.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'register.html', {
                'departments': departments_list,
                'form': request.POST
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role='student'
        )

        if first_name and last_name and department_id:
            dept = Department.objects.filter(id=department_id).first()
            if dept:
                roll_number = f"STU{datetime.utcnow().year}{User.objects.count():04d}"
                Student.objects.create(
                    roll_number=roll_number,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    department=dept,
                    user=user
                )

        messages.success(request, 'Account created successfully! Please log in.')
        return redirect('login')

    return render(request, 'register.html', {'departments': departments_list, 'form': {}})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_page = request.GET.get('next') or request.POST.get('next')
            return redirect(next_page or 'home')
        messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


# ------------------------------------------------------------------
# Department Views
# ------------------------------------------------------------------
def departments(request):
    all_departments = Department.objects.order_by('name')
    return render(request, 'departments.html', {'departments': all_departments})


@admin_required
def add_department(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().upper()
        head = request.POST.get('head_of_department', '').strip()
        description = request.POST.get('description', '').strip()

        if not name or not code:
            messages.error(request, 'Name and code are required.')
            return render(request, 'department_form.html', {'form': request.POST})

        if Department.objects.filter(name=name).exists() or Department.objects.filter(code=code).exists():
            messages.error(request, 'A department with that name or code already exists.')
            return render(request, 'department_form.html', {'form': request.POST})

        Department.objects.create(
            name=name,
            code=code,
            head_of_department=head,
            description=description
        )
        messages.success(request, 'Department added successfully.')
        return redirect('departments')

    return render(request, 'department_form.html', {'form': {}})


@admin_required
def edit_department(request, dept_id):
    dept = get_object_or_404(Department, id=dept_id)
    if request.method == 'POST':
        dept.name = request.POST.get('name', '').strip()
        dept.code = request.POST.get('code', '').strip().upper()
        dept.head_of_department = request.POST.get('head_of_department', '').strip()
        dept.description = request.POST.get('description', '').strip()
        dept.save()
        messages.success(request, 'Department updated successfully.')
        return redirect('departments')
    return render(request, 'department_form.html', {'form': dept, 'editing': True})


@admin_required
def delete_department(request, dept_id):
    if request.method == 'POST':
        dept = get_object_or_404(Department, id=dept_id)
        dept.delete()
        messages.info(request, 'Department deleted.')
    return redirect('departments')


# ------------------------------------------------------------------
# Course Views
# ------------------------------------------------------------------
def courses(request):
    all_courses = Course.objects.order_by('name')
    return render(request, 'courses.html', {'courses': all_courses})


def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    is_registered = False
    if request.user.is_authenticated:
        student = getattr(request.user, 'student_profile', None)
        if student:
            is_registered = Registration.objects.filter(
                student=student,
                course=course
            ).exists()
    return render(request, 'course_detail.html', {'course': course, 'is_registered': is_registered})


@admin_required
def add_course(request):
    departments_list = Department.objects.order_by('name')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().upper()
        credits = request.POST.get('credits', 3)
        duration_weeks = request.POST.get('duration_weeks', 16)
        description = request.POST.get('description', '').strip()
        department_id = request.POST.get('department_id')

        if not name or not code or not department_id:
            messages.error(request, 'Name, code and department are required.')
            return render(request, 'course_form.html', {
                'departments': departments_list,
                'form': request.POST
            })

        if Course.objects.filter(code=code).exists():
            messages.error(request, 'A course with that code already exists.')
            return render(request, 'course_form.html', {
                'departments': departments_list,
                'form': request.POST
            })

        dept = get_object_or_404(Department, id=department_id)
        Course.objects.create(
            name=name,
            code=code,
            credits=credits or 3,
            duration_weeks=duration_weeks or 16,
            description=description,
            department=dept
        )
        messages.success(request, 'Course added successfully.')
        return redirect('courses')

    return render(request, 'course_form.html', {'departments': departments_list, 'form': {}})


@admin_required
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    departments_list = Department.objects.order_by('name')
    if request.method == 'POST':
        course.name = request.POST.get('name', '').strip()
        course.code = request.POST.get('code', '').strip().upper()
        course.credits = request.POST.get('credits', 3) or 3
        course.duration_weeks = request.POST.get('duration_weeks', 16) or 16
        course.description = request.POST.get('description', '').strip()
        dept_id = request.POST.get('department_id')
        if dept_id:
            course.department = get_object_or_404(Department, id=dept_id)
        course.save()
        messages.success(request, 'Course updated successfully.')
        return redirect('courses')
    return render(request, 'course_form.html', {
        'departments': departments_list,
        'form': course,
        'editing': True
    })


@admin_required
def delete_course(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        course.delete()
        messages.info(request, 'Course deleted.')
    return redirect('courses')


@login_required
def register_course(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        student = getattr(request.user, 'student_profile', None)

        if not student:
            messages.error(request, 'Only students with a linked profile can register for courses.')
            return redirect('course_detail', course_id=course_id)

        existing = Registration.objects.filter(student=student, course=course).first()
        if existing:
            messages.warning(request, 'You are already registered for this course.')
        else:
            Registration.objects.create(student=student, course=course)
            messages.success(request, f'Successfully registered for {course.name}!')

    return redirect('course_detail', course_id=course_id)


@login_required
def unregister_course(request, course_id):
    if request.method == 'POST':
        student = getattr(request.user, 'student_profile', None)
        if student:
            Registration.objects.filter(student=student, course_id=course_id).delete()
            messages.info(request, 'You have unregistered from the course.')
    return redirect('course_detail', course_id=course_id)


@login_required
def my_courses(request):
    student = getattr(request.user, 'student_profile', None)
    if not student:
        messages.warning(request, 'No student profile linked to this account.')
        return redirect('home')
    return render(request, 'my_courses.html', {'student': student})


# ------------------------------------------------------------------
# Student Views
# ------------------------------------------------------------------
@login_required
def students(request):
    all_students = Student.objects.order_by('first_name')
    return render(request, 'students.html', {'students': all_students})


@login_required
def student_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    return render(request, 'student_detail.html', {'student': student})


@admin_required
def add_student(request):
    departments_list = Department.objects.order_by('name')
    if request.method == 'POST':
        roll_number = request.POST.get('roll_number', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        gender = request.POST.get('gender', '')
        address = request.POST.get('address', '').strip()
        department_id = request.POST.get('department_id')
        enrollment_year = request.POST.get('enrollment_year') or datetime.utcnow().year

        if not roll_number or not first_name or not last_name or not email or not department_id:
            messages.error(request, 'Roll number, name, email and department are required.')
            return render(request, 'student_form.html', {
                'departments': departments_list,
                'form': request.POST
            })

        if Student.objects.filter(roll_number=roll_number).exists() or Student.objects.filter(email=email).exists():
            messages.error(request, 'A student with that roll number or email already exists.')
            return render(request, 'student_form.html', {
                'departments': departments_list,
                'form': request.POST
            })

        dept = get_object_or_404(Department, id=department_id)
        Student.objects.create(
            roll_number=roll_number,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            gender=gender,
            address=address,
            department=dept,
            enrollment_year=enrollment_year
        )
        messages.success(request, 'Student added successfully.')
        return redirect('students')

    return render(request, 'student_form.html', {'departments': departments_list, 'form': {}})


@admin_required
def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    departments_list = Department.objects.order_by('name')
    if request.method == 'POST':
        student.roll_number = request.POST.get('roll_number', '').strip()
        student.first_name = request.POST.get('first_name', '').strip()
        student.last_name = request.POST.get('last_name', '').strip()
        student.email = request.POST.get('email', '').strip()
        student.phone = request.POST.get('phone', '').strip()
        student.gender = request.POST.get('gender', '')
        student.address = request.POST.get('address', '').strip()
        dept_id = request.POST.get('department_id')
        if dept_id:
            student.department = get_object_or_404(Department, id=dept_id)
        student.enrollment_year = request.POST.get('enrollment_year') or student.enrollment_year
        student.save()
        messages.success(request, 'Student updated successfully.')
        return redirect('students')
    return render(request, 'student_form.html', {
        'departments': departments_list,
        'form': student,
        'editing': True
    })


@admin_required
def delete_student(request, student_id):
    if request.method == 'POST':
        student = get_object_or_404(Student, id=student_id)
        student.delete()
        messages.info(request, 'Student deleted.')
    return redirect('students')


# ------------------------------------------------------------------
# Attendance Views
# ------------------------------------------------------------------
@login_required
def attendance_dashboard(request):
    is_admin_user = (request.user.role == 'admin' or request.user.is_staff or request.user.is_superuser)
    if not is_admin_user:
        return redirect('my_attendance')

    courses = Course.objects.select_related('department').all()
    course_data = []
    for c in courses:
        total_sessions = Attendance.objects.filter(course=c).values('date').distinct().count()
        total_records = Attendance.objects.filter(course=c).count()
        present_records = Attendance.objects.filter(course=c, status__in=['Present', 'Late']).count()
        avg_pct = round((present_records / total_records * 100), 1) if total_records > 0 else 0
        course_data.append({
            'course': c,
            'enrolled_count': c.enrolled_count,
            'total_sessions': total_sessions,
            'avg_attendance': avg_pct,
        })

    today_str = date.today().strftime('%Y-%m-%d')
    return render(request, 'attendance_dashboard.html', {
        'course_data': course_data,
        'today_str': today_str,
    })


@admin_required
def mark_attendance(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    registrations = Registration.objects.filter(course=course).select_related('student')

    selected_date_str = request.GET.get('date') or request.POST.get('date') or date.today().strftime('%Y-%m-%d')
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = date.today()
        selected_date_str = selected_date.strftime('%Y-%m-%d')

    if request.method == 'POST':
        saved_count = 0
        for reg in registrations:
            student = reg.student
            status = request.POST.get(f"status_{student.id}", "Present")
            remarks = request.POST.get(f"remarks_{student.id}", "").strip()

            Attendance.objects.update_or_create(
                course=course,
                student=student,
                date=selected_date,
                defaults={
                    'status': status,
                    'remarks': remarks,
                    'recorded_by': request.user,
                }
            )
            saved_count += 1

        messages.success(request, f'Attendance for {course.code} on {selected_date.strftime("%b %d, %Y")} saved ({saved_count} students).')
        return redirect(f"{reverse('mark_attendance', args=[course.id])}?date={selected_date_str}")

    # For GET: Fetch existing attendance records for this date
    existing_attendance = {
        att.student_id: att
        for att in Attendance.objects.filter(course=course, date=selected_date)
    }

    students_sheet = []
    for reg in registrations:
        att = existing_attendance.get(reg.student.id)
        students_sheet.append({
            'student': reg.student,
            'status': att.status if att else 'Present',
            'remarks': att.remarks if att else '',
        })

    return render(request, 'mark_attendance.html', {
        'course': course,
        'selected_date': selected_date,
        'selected_date_str': selected_date_str,
        'students_sheet': students_sheet,
        'status_choices': Attendance.STATUS_CHOICES,
        'today_str': date.today().strftime('%Y-%m-%d'),
    })


@admin_required
def course_attendance_report(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    registrations = Registration.objects.filter(course=course).select_related('student')
    distinct_dates = list(
        Attendance.objects.filter(course=course)
        .values_list('date', flat=True)
        .distinct()
        .order_by('-date')
    )
    total_sessions = len(distinct_dates)

    student_reports = []
    for reg in registrations:
        st = reg.student
        records = Attendance.objects.filter(course=course, student=st)
        present_count = records.filter(status__in=['Present', 'Late']).count()
        absent_count = records.filter(status='Absent').count()
        percentage = round((present_count / total_sessions * 100), 1) if total_sessions > 0 else 0
        student_reports.append({
            'student': st,
            'present_count': present_count,
            'absent_count': absent_count,
            'percentage': percentage,
            'is_low': percentage < 75 if total_sessions > 0 else False,
        })

    overall_present = Attendance.objects.filter(course=course, status__in=['Present', 'Late']).count()
    overall_total = Attendance.objects.filter(course=course).count()
    overall_pct = round((overall_present / overall_total * 100), 1) if overall_total > 0 else 0

    return render(request, 'course_attendance_report.html', {
        'course': course,
        'total_sessions': total_sessions,
        'distinct_dates': distinct_dates[:10],
        'student_reports': student_reports,
        'overall_pct': overall_pct,
    })


@login_required
def my_attendance(request):
    student = getattr(request.user, 'student_profile', None)
    if not student:
        student = Student.objects.filter(email=request.user.email).first()

    if not student:
        messages.info(request, 'No student profile linked to your user account.')
        return render(request, 'my_attendance.html', {'student': None, 'course_stats': []})

    registrations = Registration.objects.filter(student=student).select_related('course')
    course_stats = []
    total_classes_all = 0
    total_attended_all = 0

    for reg in registrations:
        c = reg.course
        total_sessions = Attendance.objects.filter(course=c).values('date').distinct().count()
        student_att = Attendance.objects.filter(course=c, student=student)
        attended_count = student_att.filter(status__in=['Present', 'Late']).count()
        absent_count = student_att.filter(status='Absent').count()
        pct = round((attended_count / total_sessions * 100), 1) if total_sessions > 0 else 0
        recent_logs = student_att.order_by('-date')[:10]

        total_classes_all += total_sessions
        total_attended_all += attended_count

        course_stats.append({
            'course': c,
            'total_sessions': total_sessions,
            'attended_count': attended_count,
            'absent_count': absent_count,
            'percentage': pct,
            'is_low': pct < 75 if total_sessions > 0 else False,
            'recent_logs': recent_logs,
        })

    overall_pct = round((total_attended_all / total_classes_all * 100), 1) if total_classes_all > 0 else 0

    return render(request, 'my_attendance.html', {
        'student': student,
        'course_stats': course_stats,
        'total_classes_all': total_classes_all,
        'total_attended_all': total_attended_all,
        'overall_pct': overall_pct,
    })


# ------------------------------------------------------------------
# Voting / Election Views
# ------------------------------------------------------------------
@login_required
def elections_list(request):
    all_elections = Election.objects.prefetch_related('positions__candidates').all()

    user_voted_elections = set(
        Vote.objects.filter(voter=request.user)
        .values_list('position__election_id', flat=True)
        .distinct()
    )

    elections_data = []
    for el in all_elections:
        has_voted = el.id in user_voted_elections
        elections_data.append({
            'election': el,
            'status_label': el.status_label,
            'is_voting_open': el.is_voting_open,
            'has_voted': has_voted,
            'positions_count': el.positions.count(),
            'total_votes': el.total_votes_cast,
        })

    return render(request, 'elections_list.html', {
        'elections_data': elections_data,
        'is_admin': request.user.role == 'admin' or request.user.is_staff or request.user.is_superuser,
    })


@login_required
def election_ballot(request, election_id):
    election = get_object_or_404(Election, id=election_id)
    positions = election.positions.prefetch_related('candidates').all()

    already_voted = Vote.objects.filter(position__election=election, voter=request.user).exists()
    if already_voted:
        messages.info(request, 'You have already cast your vote in this election! Showing results.')
        return redirect('election_results', election_id=election.id)

    if not election.is_voting_open:
        messages.warning(request, f'Voting is currently not open for this election ({election.status_label}).')
        return redirect('election_results', election_id=election.id)

    if request.method == 'POST':
        votes_to_create = []
        errors = []

        for pos in positions:
            candidate_id = request.POST.get(f"position_{pos.id}")
            if not candidate_id:
                errors.append(f"Please select a candidate for '{pos.title}'.")
            else:
                candidate = pos.candidates.filter(id=candidate_id).first()
                if not candidate:
                    errors.append(f"Invalid candidate selected for '{pos.title}'.")
                else:
                    votes_to_create.append((pos, candidate))

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'election_ballot.html', {
                'election': election,
                'positions': positions,
            })

        try:
            with transaction.atomic():
                if Vote.objects.filter(position__election=election, voter=request.user).exists():
                    messages.error(request, 'You have already voted in this election.')
                    return redirect('election_results', election_id=election.id)

                for pos, cand in votes_to_create:
                    Vote.objects.create(
                        position=pos,
                        candidate=cand,
                        voter=request.user
                    )
            messages.success(request, '🎉 Your vote has been recorded successfully! Thank you for participating.')
            return redirect('election_results', election_id=election.id)
        except Exception as e:
            messages.error(request, f'An error occurred while saving your vote: {e}')

    return render(request, 'election_ballot.html', {
        'election': election,
        'positions': positions,
    })


@login_required
def election_results(request, election_id):
    election = get_object_or_404(Election, id=election_id)
    positions = election.positions.prefetch_related('candidates__votes').all()

    has_voted = Vote.objects.filter(position__election=election, voter=request.user).exists()

    positions_data = []
    for pos in positions:
        total_pos_votes = pos.total_votes
        candidates_list = []
        max_votes = -1

        for cand in pos.candidates.all():
            cnt = cand.vote_count
            pct = round((cnt / total_pos_votes * 100), 1) if total_pos_votes > 0 else 0
            cand_info = {
                'candidate': cand,
                'votes': cnt,
                'percentage': pct,
                'is_winner': False,
            }
            candidates_list.append(cand_info)
            if cnt > max_votes and cnt > 0:
                max_votes = cnt

        if max_votes > 0:
            for c in candidates_list:
                if c['votes'] == max_votes:
                    c['is_winner'] = True

        candidates_list.sort(key=lambda x: x['votes'], reverse=True)

        positions_data.append({
            'position': pos,
            'total_votes': total_pos_votes,
            'candidates': candidates_list,
        })

    return render(request, 'election_results.html', {
        'election': election,
        'positions_data': positions_data,
        'has_voted': has_voted,
        'is_admin': request.user.role == 'admin' or request.user.is_staff or request.user.is_superuser,
    })


@admin_required
def admin_elections(request):
    elections = Election.objects.prefetch_related('positions__candidates').all()
    students = Student.objects.order_by('first_name', 'last_name')
    return render(request, 'admin_elections.html', {
        'elections': elections,
        'students': students,
    })


@admin_required
def add_election(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')

        if not title or not start_date_str or not end_date_str:
            messages.error(request, 'Title, start date, and end date are required.')
            return redirect('admin_elections')

        try:
            start_date = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M'))
            end_date = timezone.make_aware(datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M'))
        except (ValueError, TypeError):
            messages.error(request, 'Invalid date format.')
            return redirect('admin_elections')

        if end_date <= start_date:
            messages.error(request, 'End date must be after start date.')
            return redirect('admin_elections')

        Election.objects.create(
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )
        messages.success(request, f'Election "{title}" created! You can now add positions and candidates below.')
    return redirect('admin_elections')


@admin_required
def toggle_election(request, election_id):
    election = get_object_or_404(Election, id=election_id)
    if request.method == 'POST':
        election.is_active = not election.is_active
        election.save()
        status_txt = "activated" if election.is_active else "deactivated"
        messages.info(request, f'Election "{election.title}" {status_txt}.')
    return redirect('admin_elections')


@admin_required
def add_position(request, election_id):
    election = get_object_or_404(Election, id=election_id)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        display_order = request.POST.get('display_order', 0)
        if title:
            ElectionPosition.objects.create(
                election=election,
                title=title,
                description=description,
                display_order=int(display_order or 0)
            )
            messages.success(request, f'Position "{title}" added to {election.title}.')
        else:
            messages.error(request, 'Position title is required.')
    return redirect('admin_elections')


@admin_required
def add_candidate(request, position_id):
    position = get_object_or_404(ElectionPosition, id=position_id)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        manifesto = request.POST.get('manifesto', '').strip()
        symbol_icon = request.POST.get('symbol_icon', 'bi-award-fill').strip()
        student_id = request.POST.get('student_id')

        student = None
        if student_id:
            student = Student.objects.filter(id=student_id).first()
            if student and not name:
                name = student.full_name

        if name:
            Candidate.objects.create(
                position=position,
                student=student,
                name=name,
                manifesto=manifesto,
                symbol_icon=symbol_icon or 'bi-award-fill'
            )
            messages.success(request, f'Candidate "{name}" added for position "{position.title}".')
        else:
            messages.error(request, 'Candidate name is required.')
    return redirect('admin_elections')

