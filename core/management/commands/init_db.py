import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import (
    User, Department, Course, Student, Registration,
    Attendance, Election, ElectionPosition, Candidate
)


class Command(BaseCommand):
    help = 'Create admin user, sample students, courses, attendance, and election data'

    def handle(self, *args, **options):
        # 1. Admin User
        admin_user = User.objects.filter(username='admin').first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@campus.edu',
                password='admin123',
                role='admin'
            )
            self.stdout.write(self.style.SUCCESS("Admin user created (admin / admin123)."))
        else:
            self.stdout.write("Admin user already exists.")

        # 2. Departments & Courses
        cse, _ = Department.objects.get_or_create(
            code='CSE',
            defaults={
                'name': 'Computer Science & Engineering',
                'head_of_department': 'Dr. A. Rao',
                'description': 'Focuses on software, AI and systems.'
            }
        )
        ece, _ = Department.objects.get_or_create(
            code='ECE',
            defaults={
                'name': 'Electronics & Communication',
                'head_of_department': 'Dr. S. Kumar',
                'description': 'Focuses on electronics and communication systems.'
            }
        )
        mech, _ = Department.objects.get_or_create(
            code='MECH',
            defaults={
                'name': 'Mechanical Engineering',
                'head_of_department': 'Dr. P. Sharma',
                'description': 'Focuses on mechanical design and manufacturing.'
            }
        )

        c_dsa, _ = Course.objects.get_or_create(
            code='CSE201',
            defaults={
                'name': 'Data Structures & Algorithms',
                'credits': 4,
                'duration_weeks': 16,
                'description': 'Core data structures, algorithms and complexity analysis.',
                'department': cse
            }
        )
        c_ml, _ = Course.objects.get_or_create(
            code='CSE305',
            defaults={
                'name': 'Machine Learning',
                'credits': 4,
                'duration_weeks': 16,
                'description': 'Supervised, unsupervised learning and neural networks.',
                'department': cse
            }
        )
        c_dsp, _ = Course.objects.get_or_create(
            code='ECE210',
            defaults={
                'name': 'Digital Signal Processing',
                'credits': 3,
                'duration_weeks': 14,
                'description': 'Signal analysis and processing techniques.',
                'department': ece
            }
        )

        # 3. Sample Student Users
        stu_user1, _ = User.objects.get_or_create(
            username='rahul',
            defaults={'email': 'rahul@student.edu', 'role': 'student'}
        )
        if _:
            stu_user1.set_password('student123')
            stu_user1.save()

        student1, _ = Student.objects.get_or_create(
            roll_number='STU2026001',
            defaults={
                'first_name': 'Rahul',
                'last_name': 'Sharma',
                'email': 'rahul@student.edu',
                'department': cse,
                'user': stu_user1,
                'enrollment_year': 2026
            }
        )

        stu_user2, _ = User.objects.get_or_create(
            username='priya',
            defaults={'email': 'priya@student.edu', 'role': 'student'}
        )
        if _:
            stu_user2.set_password('student123')
            stu_user2.save()

        student2, _ = Student.objects.get_or_create(
            roll_number='STU2026002',
            defaults={
                'first_name': 'Priya',
                'last_name': 'Patel',
                'email': 'priya@student.edu',
                'department': cse,
                'user': stu_user2,
                'enrollment_year': 2026
            }
        )

        # 4. Registrations
        Registration.objects.get_or_create(student=student1, course=c_dsa, defaults={'status': 'Active'})
        Registration.objects.get_or_create(student=student1, course=c_ml, defaults={'status': 'Active'})
        Registration.objects.get_or_create(student=student2, course=c_dsa, defaults={'status': 'Active'})
        Registration.objects.get_or_create(student=student2, course=c_dsp, defaults={'status': 'Active'})

        # 5. Sample Attendance Logs
        today = datetime.date.today()
        dates = [today - datetime.timedelta(days=i) for i in [5, 4, 3, 2, 1, 0]]

        for d in dates:
            # DSA
            Attendance.objects.get_or_create(
                course=c_dsa, student=student1, date=d,
                defaults={'status': 'Present', 'recorded_by': admin_user}
            )
            Attendance.objects.get_or_create(
                course=c_dsa, student=student2, date=d,
                defaults={'status': 'Present' if d != dates[1] else 'Absent', 'recorded_by': admin_user}
            )
            # ML
            Attendance.objects.get_or_create(
                course=c_ml, student=student1, date=d,
                defaults={'status': 'Present' if d != dates[3] else 'Late', 'recorded_by': admin_user}
            )

        # 6. Sample Student Council Election
        election, _ = Election.objects.get_or_create(
            title='Student Council General Elections 2026',
            defaults={
                'description': 'Annual student council elections for institutional student leadership and representation.',
                'start_date': timezone.now() - datetime.timedelta(days=1),
                'end_date': timezone.now() + datetime.timedelta(days=6),
                'is_active': True,
            }
        )

        pos_pres, _ = ElectionPosition.objects.get_or_create(
            election=election,
            title='President',
            defaults={
                'description': 'Leads the Student Council, liaises with administration, and advocates for student welfare.',
                'display_order': 1
            }
        )

        pos_sec, _ = ElectionPosition.objects.get_or_create(
            election=election,
            title='General Secretary',
            defaults={
                'description': 'Coordinates campus events, inter-departmental fests, and student activities.',
                'display_order': 2
            }
        )

        Candidate.objects.get_or_create(
            position=pos_pres,
            name='Rahul Sharma',
            defaults={
                'student': student1,
                'manifesto': 'Committed to 24x7 library access, improved lab equipment, and enhanced campus Wi-Fi.',
                'symbol_icon': 'bi-trophy-fill'
            }
        )
        Candidate.objects.get_or_create(
            position=pos_pres,
            name='Ananya Verma',
            defaults={
                'manifesto': 'Promoting hackathons, industry mentorship programs, and green campus initiatives.',
                'symbol_icon': 'bi-star-fill'
            }
        )

        Candidate.objects.get_or_create(
            position=pos_sec,
            name='Priya Patel',
            defaults={
                'student': student2,
                'manifesto': 'Dedicated to transparent club budgeting and organizing an epic annual cultural fest.',
                'symbol_icon': 'bi-award-fill'
            }
        )
        Candidate.objects.get_or_create(
            position=pos_sec,
            name='Karan Mehta',
            defaults={
                'manifesto': 'Expanding sports facilities, indoor tournaments, and technical symposiums.',
                'symbol_icon': 'bi-shield-check'
            }
        )

        self.stdout.write(self.style.SUCCESS("Database successfully initialized with admin, students, attendance logs, and sample election!"))

