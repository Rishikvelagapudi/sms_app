import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('student', 'Student'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

    def __str__(self):
        return f"{self.username} ({self.role})"


class Department(models.Model):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=20, unique=True)
    head_of_department = models.CharField(max_length=120, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def student_count(self):
        return self.students.count()

    @property
    def course_count(self):
        return self.courses.count()


class Course(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)
    credits = models.IntegerField(default=3)
    duration_weeks = models.IntegerField(default=16)
    description = models.TextField(blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def enrolled_count(self):
        return self.registrations.count()


def current_year():
    return datetime.date.today().year


class Student(models.Model):
    roll_number = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    email = models.EmailField(max_length=120, unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    enrollment_year = models.IntegerField(default=current_year)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='students')
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_profile'
    )

    class Meta:
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.full_name} ({self.roll_number})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Registration(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='registrations')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='registrations')
    registered_on = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Active')

    class Meta:
        unique_together = ('student', 'course')
        ordering = ['-registered_on']

    def __str__(self):
        return f"{self.student.full_name} - {self.course.code}"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
        ('Excused', 'Excused'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=datetime.date.today)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Present')
    remarks = models.CharField(max_length=255, blank=True, null=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_attendances'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'student', 'date')
        ordering = ['-date', 'student__first_name', 'student__last_name']

    def __str__(self):
        return f"{self.student.full_name} - {self.course.code} ({self.date}): {self.status}"


class Election(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def status_label(self):
        now = timezone.now()
        if not self.is_active:
            return 'Inactive'
        if now < self.start_date:
            return 'Upcoming'
        elif self.start_date <= now <= self.end_date:
            return 'Ongoing'
        else:
            return 'Ended'

    @property
    def is_voting_open(self):
        now = timezone.now()
        return self.is_active and (self.start_date <= now <= self.end_date)

    @property
    def total_votes_cast(self):
        return Vote.objects.filter(position__election=self).count()

    @property
    def unique_voters_count(self):
        return Vote.objects.filter(position__election=self).values('voter').distinct().count()


class ElectionPosition(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='positions')
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'title']

    def __str__(self):
        return f"{self.title} ({self.election.title})"

    @property
    def total_votes(self):
        return self.votes.count()


class Candidate(models.Model):
    position = models.ForeignKey(ElectionPosition, on_delete=models.CASCADE, related_name='candidates')
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='candidacies')
    name = models.CharField(max_length=150)
    manifesto = models.TextField(blank=True, null=True)
    symbol_icon = models.CharField(max_length=50, default='bi-person-badge', help_text="Bootstrap icon name like bi-award-fill, bi-star-fill, etc.")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.position.title}"

    @property
    def vote_count(self):
        return self.votes.count()

    @property
    def vote_percentage(self):
        pos_votes = self.position.total_votes
        if pos_votes == 0:
            return 0
        return round((self.vote_count / pos_votes) * 100, 1)


class Vote(models.Model):
    position = models.ForeignKey(ElectionPosition, on_delete=models.CASCADE, related_name='votes')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='votes')
    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='votes')
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('position', 'voter')
        ordering = ['-voted_at']

    def __str__(self):
        return f"Vote by {self.voter.username} for {self.candidate.name} ({self.position.title})"

