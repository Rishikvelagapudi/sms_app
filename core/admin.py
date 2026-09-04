from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Department, Course, Student, Registration,
    Attendance, Election, ElectionPosition, Candidate, Vote
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )
    list_display = ['username', 'email', 'role', 'is_staff', 'is_superuser']
    list_filter = ['role', 'is_staff', 'is_superuser']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'head_of_department', 'course_count', 'student_count']
    search_fields = ['name', 'code', 'head_of_department']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'credits', 'duration_weeks', 'enrolled_count']
    list_filter = ['department', 'credits']
    search_fields = ['name', 'code']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['roll_number', 'full_name', 'email', 'department', 'enrollment_year']
    list_filter = ['department', 'enrollment_year', 'gender']
    search_fields = ['roll_number', 'first_name', 'last_name', 'email']


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'registered_on', 'status']
    list_filter = ['status', 'registered_on']
    search_fields = ['student__first_name', 'student__last_name', 'student__roll_number', 'course__name', 'course__code']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'date', 'status', 'recorded_by']
    list_filter = ['status', 'date', 'course']
    search_fields = ['student__first_name', 'student__last_name', 'student__roll_number', 'course__name', 'course__code']


class CandidateInline(admin.TabularInline):
    model = Candidate
    extra = 1


class ElectionPositionInline(admin.StackedInline):
    model = ElectionPosition
    extra = 1


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'start_date', 'end_date', 'is_active', 'status_label', 'total_votes_cast', 'unique_voters_count']
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['title', 'description']
    inlines = [ElectionPositionInline]


@admin.register(ElectionPosition)
class ElectionPositionAdmin(admin.ModelAdmin):
    list_display = ['title', 'election', 'display_order', 'total_votes']
    list_filter = ['election']
    search_fields = ['title', 'election__title']
    inlines = [CandidateInline]


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'student', 'vote_count', 'vote_percentage']
    list_filter = ['position__election', 'position']
    search_fields = ['name', 'position__title']


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['voter', 'candidate', 'position', 'voted_at']
    list_filter = ['position__election', 'position']
    search_fields = ['voter__username', 'candidate__name', 'position__title']

