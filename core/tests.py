from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.db import IntegrityError
from core.models import (
    User, Department, Course, Student, Registration,
    Attendance, Election, ElectionPosition, Candidate, Vote
)


class AttendanceAndVotingTests(TestCase):
    def setUp(self):
        # Admin user
        self.admin = User.objects.create_superuser(
            username='testadmin',
            email='admin@test.com',
            password='password123',
            role='admin'
        )

        # Student user
        self.student_user = User.objects.create_user(
            username='teststudent',
            email='student@test.com',
            password='password123',
            role='student'
        )

        self.dept = Department.objects.create(
            name='Computer Science',
            code='CS'
        )

        self.course = Course.objects.create(
            name='Algorithms',
            code='CS101',
            credits=3,
            department=self.dept
        )

        self.student = Student.objects.create(
            roll_number='STU1001',
            first_name='John',
            last_name='Doe',
            email='student@test.com',
            department=self.dept,
            user=self.student_user
        )

        self.reg = Registration.objects.create(
            student=self.student,
            course=self.course
        )

        self.client = Client()

    def test_attendance_creation_and_uniqueness(self):
        today = date.today()
        att = Attendance.objects.create(
            course=self.course,
            student=self.student,
            date=today,
            status='Present',
            recorded_by=self.admin
        )
        self.assertEqual(att.status, 'Present')

        # Check unique_together (course, student, date)
        with self.assertRaises(IntegrityError):
            Attendance.objects.create(
                course=self.course,
                student=self.student,
                date=today,
                status='Absent'
            )

    def test_mark_attendance_post(self):
        self.client.login(username='testadmin', password='password123')
        target_date = (date.today() - timedelta(days=2)).strftime('%Y-%m-%d')

        response = self.client.post(
            reverse('mark_attendance', args=[self.course.id]),
            {
                'date': target_date,
                f'status_{self.student.id}': 'Present',
                f'remarks_{self.student.id}': 'Good'
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)

        record = Attendance.objects.filter(
            course=self.course,
            student=self.student,
            date=target_date
        ).first()
        self.assertIsNotNone(record)
        self.assertEqual(record.status, 'Present')
        self.assertEqual(record.remarks, 'Good')

    def test_student_my_attendance_view(self):
        # Create attendance record
        Attendance.objects.create(
            course=self.course,
            student=self.student,
            date=date.today(),
            status='Present'
        )

        self.client.login(username='teststudent', password='password123')
        response = self.client.get(reverse('my_attendance'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Algorithms')
        self.assertContains(response, '100.0%')

    def test_election_voting_flow_and_double_voting_prevention(self):
        now = timezone.now()
        election = Election.objects.create(
            title='Campus Council 2026',
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=5),
            is_active=True
        )

        pos = ElectionPosition.objects.create(
            election=election,
            title='President'
        )

        cand1 = Candidate.objects.create(position=pos, name='Alice')
        cand2 = Candidate.objects.create(position=pos, name='Bob')

        self.assertTrue(election.is_voting_open)
        self.assertEqual(election.status_label, 'Ongoing')

        # Student votes for Alice
        self.client.login(username='teststudent', password='password123')
        vote_res = self.client.post(
            reverse('election_ballot', args=[election.id]),
            {f'position_{pos.id}': cand1.id},
            follow=True
        )
        self.assertEqual(vote_res.status_code, 200)

        # Alice should have 1 vote
        self.assertEqual(cand1.vote_count, 1)
        self.assertEqual(cand2.vote_count, 0)
        self.assertEqual(cand1.vote_percentage, 100.0)

        # Attempt to double-vote via POST should fail/redirect
        vote_res2 = self.client.post(
            reverse('election_ballot', args=[election.id]),
            {f'position_{pos.id}': cand2.id},
            follow=True
        )
        self.assertEqual(cand1.vote_count, 1)
        self.assertEqual(cand2.vote_count, 0)

        # Direct database-level double-vote attempt should raise IntegrityError
        with self.assertRaises(IntegrityError):
            Vote.objects.create(
                position=pos,
                candidate=cand2,
                voter=self.student_user
            )

    def test_results_page(self):
        election = Election.objects.create(
            title='Poll 2026',
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=2),
            is_active=True
        )
        pos = ElectionPosition.objects.create(election=election, title='Representative')
        Candidate.objects.create(position=pos, name='Charlie')

        self.client.login(username='teststudent', password='password123')
        res = self.client.get(reverse('election_results', args=[election.id]))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Charlie')
