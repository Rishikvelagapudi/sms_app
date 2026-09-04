from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Departments
    path('departments/', views.departments, name='departments'),
    path('departments/add/', views.add_department, name='add_department'),
    path('departments/<int:dept_id>/edit/', views.edit_department, name='edit_department'),
    path('departments/<int:dept_id>/delete/', views.delete_department, name='delete_department'),

    # Courses
    path('courses/', views.courses, name='courses'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/add/', views.add_course, name='add_course'),
    path('courses/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('courses/<int:course_id>/delete/', views.delete_course, name='delete_course'),
    path('courses/<int:course_id>/register/', views.register_course, name='register_course'),
    path('courses/<int:course_id>/unregister/', views.unregister_course, name='unregister_course'),
    path('my-courses/', views.my_courses, name='my_courses'),

    # Students
    path('students/', views.students, name='students'),
    path('students/<int:student_id>/', views.student_detail, name='student_detail'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/<int:student_id>/edit/', views.edit_student, name='edit_student'),
    path('students/<int:student_id>/delete/', views.delete_student, name='delete_student'),

    # Attendance
    path('attendance/', views.attendance_dashboard, name='attendance_dashboard'),
    path('attendance/<int:course_id>/mark/', views.mark_attendance, name='mark_attendance'),
    path('attendance/<int:course_id>/report/', views.course_attendance_report, name='course_attendance_report'),
    path('my-attendance/', views.my_attendance, name='my_attendance'),

    # Elections / Voting
    path('elections/', views.elections_list, name='elections_list'),
    path('elections/<int:election_id>/', views.election_ballot, name='election_ballot'),
    path('elections/<int:election_id>/results/', views.election_results, name='election_results'),
    path('elections/manage/', views.admin_elections, name='admin_elections'),
    path('elections/add/', views.add_election, name='add_election'),
    path('elections/<int:election_id>/toggle/', views.toggle_election, name='toggle_election'),
    path('elections/<int:election_id>/add-position/', views.add_position, name='add_position'),
    path('elections/positions/<int:position_id>/add-candidate/', views.add_candidate, name='add_candidate'),
]

