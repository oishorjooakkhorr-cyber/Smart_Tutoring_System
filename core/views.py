from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Student, Tutor, Learner, Skill, AvailableSlot, Booking, Ratings, Badge


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")
    else:
        form = AuthenticationForm()

    return render(request, "login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required(login_url="login")
def home(request):
    return render(request, "home.html")


@login_required(login_url="login")
def students(request):
    data = Student.objects.select_related("department").all()
    return render(request, "students.html", {"students": data})


@login_required(login_url="login")
def tutors(request):
    data = Tutor.objects.select_related("student").all()
    return render(request, "tutors.html", {"tutors": data})


@login_required(login_url="login")
def learners(request):
    data = Learner.objects.select_related("student").all()
    return render(request, "learners.html", {"learners": data})


@login_required(login_url="login")
def skills(request):
    data = Skill.objects.all()
    return render(request, "skills.html", {"skills": data})


@login_required(login_url="login")
def slots(request):
    data = AvailableSlot.objects.select_related("tutor__student").all()
    return render(request, "slots.html", {"slots": data})


@login_required(login_url="login")
def bookings(request):
    data = Booking.objects.select_related("learner__student", "tutor__student", "slot").all()
    return render(request, "bookings.html", {"bookings": data})


@login_required(login_url="login")
def ratings(request):
    data = Ratings.objects.select_related("learner__student", "tutor__student", "booking").all()
    return render(request, "ratings.html", {"ratings": data})


@login_required(login_url="login")
def badges(request):
    data = Badge.objects.all()
    return render(request, "badges.html", {"badges": data})



# Feature 1 -> slot booking
@login_required(login_url="login")
def book_slot(request, slot_id):
    slot = get_object_or_404(AvailableSlot, slot_no=slot_id)
    
    # Get or default to the first learner profile available
    try:
        learner = Learner.objects.get(student__email=request.user.email)
    except Learner.DoesNotExist:
        learner = Learner.objects.first()

    # ONLY process creation and redirect when the user clicks the "Confirm & Book" button (POST request)
    if request.method == "POST":
        Booking.objects.create(
            learner=learner,
            tutor=slot.tutor,
            slot=slot,
            date=slot.date,
            status="Confirmed"
        )
        return redirect("bookings")

    # Render the confirmation page on GET requests
    return render(request, "book_slot.html", {"slot": slot})

