from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('tutors/', views.tutors, name='tutors'),
    path('learners/', views.learners, name='learners'),
    path('skills/', views.skills, name='skills'),
    path('slots/', views.slots, name='slots'),
    path('slots/add/', views.add_slot, name='add_slot'),
    path('bookings/', views.bookings, name='bookings'),
    path('ratings/', views.ratings, name='ratings'),
    path('badges/', views.badges, name='badges'),
    path('warnings/', views.warnings_view, name='warnings'),
    path('book_slot/<int:slot_id>/', views.book_slot, name='book_slot'),
    path('rate_booking/<int:booking_id>/', views.rate_booking, name='rate_booking'),
    path('slots/delete/<int:slot_id>/', views.delete_slot, name='delete_slot'),
    path('ratings/delete/<int:rating_id>/', views.delete_rating, name='delete_rating'),
    path('manage-skills/', views.manage_skills, name='manage_skills'),
    path('upgrade-role/', views.upgrade_role, name='upgrade_role'),
    path('bookings/confirm/<int:booking_id>/', views.confirm_booking, name='confirm_booking'),
    path('bookings/reject/<int:booking_id>/', views.reject_booking, name='reject_booking'),
    path('bookings/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
]
