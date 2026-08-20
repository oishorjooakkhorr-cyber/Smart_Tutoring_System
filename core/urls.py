from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.home, name="home"),
    path("students/", views.students, name="students"),
    path("tutors/", views.tutors, name="tutors"),
    path("learners/", views.learners, name="learners"),
    path("skills/", views.skills, name="skills"),
    path("slots/", views.slots, name="slots"),
    path("bookings/", views.bookings, name="bookings"),
    path("ratings/", views.ratings, name="ratings"),
    path("badges/", views.badges, name="badges"),
    path("book/<int:slot_id>/", views.book_slot, name="book_slot"),
]