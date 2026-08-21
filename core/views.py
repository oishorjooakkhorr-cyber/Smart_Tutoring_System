from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import Http404


def dictfetchall(cursor):
    """Return all rows from a cursor as a dict list."""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def dictfetchone(cursor):
    """Return a single row from a cursor as a dict."""
    columns = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    if row:
        return dict(zip(columns, row))
    return None


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
    query = """
        SELECT s.*, d.dept_name 
        FROM core_student s
        JOIN core_department d ON s.department_id = d.dept_id
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        data = dictfetchall(cursor)

    # Attach department dictionary structure for template compatibility
    for row in data:
        row["department"] = {"dept_name": row["dept_name"]}

    return render(request, "students.html", {"students": data})


@login_required(login_url="login")
def tutors(request):
    search_query = request.GET.get("q", "")
    status_filter = request.GET.get("status", "")

    sql = """
        SELECT t.*, s.name, s.email, s.phone, s.semester
        FROM core_tutor t
        JOIN core_student s ON t.student_id = s.sid
        WHERE 1=1
    """
    params = []

    if search_query:
        sql += " AND s.name LIKE %s"
        params.append(f"%{search_query}%")

    if status_filter:
        sql += " AND t.tutor_status = %s"
        params.append(status_filter)

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        data = dictfetchall(cursor)

    for row in data:
        row["student"] = {"name": row["name"], "email": row["email"], "phone": row["phone"]}

    return render(
        request,
        "tutors.html",
        {"tutors": data, "query": search_query, "status": status_filter},
    )


@login_required(login_url="login")
def learners(request):
    query = """
        SELECT l.*, s.name, s.email, s.phone 
        FROM core_learner l
        JOIN core_student s ON l.student_id = s.sid
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        data = dictfetchall(cursor)

    for row in data:
        row["student"] = {"name": row["name"], "email": row["email"]}

    return render(request, "learners.html", {"learners": data})


@login_required(login_url="login")
def skills(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM core_skill")
        data = dictfetchall(cursor)

    return render(request, "skills.html", {"skills": data})


@login_required(login_url="login")
def slots(request):
    query = """
        SELECT slot.*, s.name AS student_name
        FROM core_availableslot slot
        JOIN core_tutor t ON slot.tutor_id = t.student_id
        JOIN core_student s ON t.student_id = s.sid
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        data = dictfetchall(cursor)

    for row in data:
        row["tutor"] = {"student": {"name": row["student_name"]}}

    return render(request, "slots.html", {"slots": data})


@login_required(login_url="login")
def bookings(request):
    query = """
        SELECT b.*, 
               ls.name AS learner_name, 
               ts.name AS tutor_name,
               slot.slot_no, slot.start_time, slot.end_time, slot.mode
        FROM core_booking b
        JOIN core_learner l ON b.learner_id = l.student_id
        JOIN core_student ls ON l.student_id = ls.sid
        JOIN core_tutor t ON b.tutor_id = t.student_id
        JOIN core_student ts ON t.student_id = ts.sid
        JOIN core_availableslot slot ON b.slot_id = slot.id
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        data = dictfetchall(cursor)

    for row in data:
        row["learner"] = {"student": {"name": row["learner_name"]}}
        row["tutor"] = {"student": {"name": row["tutor_name"]}}
        row["slot"] = {
            "slot_no": row["slot_no"],
            "start_time": row["start_time"],
            "end_time": row["end_time"],
            "mode": row["mode"],
        }

    return render(request, "bookings.html", {"bookings": data})


@login_required(login_url="login")
def ratings(request):
    query = """
        SELECT r.*, 
               ls.name AS learner_name, 
               ts.name AS tutor_name
        FROM core_ratings r
        JOIN core_learner l ON r.learner_id = l.student_id
        JOIN core_student ls ON l.student_id = ls.sid
        JOIN core_tutor t ON r.tutor_id = t.student_id
        JOIN core_student ts ON t.student_id = ts.sid
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        data = dictfetchall(cursor)

    for row in data:
        row["learner"] = {"student": {"name": row["learner_name"]}}
        row["tutor"] = {"student": {"name": row["tutor_name"]}}

    return render(request, "ratings.html", {"ratings": data})


@login_required(login_url="login")
def badges(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM core_badge")
        data = dictfetchall(cursor)

    return render(request, "badges.html", {"badges": data})


# Feature 1 -> slot booking with Raw SQL
@login_required(login_url="login")
def book_slot(request, slot_id):
    with connection.cursor() as cursor:
        # Fetch target slot using slot_no
        cursor.execute(
            """
            SELECT slot.*, ts.name AS tutor_name 
            FROM core_availableslot slot
            JOIN core_tutor t ON slot.tutor_id = t.student_id
            JOIN core_student ts ON t.student_id = ts.sid
            WHERE slot.slot_no = %s
        """,
            [slot_id],
        )
        slot = dictfetchone(cursor)

        if not slot:
            raise Http404("Slot does not exist")

        slot["tutor"] = {"student": {"name": slot["tutor_name"]}}

        # Get learner profile corresponding to current logged-in user email
        cursor.execute(
            """
            SELECT l.student_id 
            FROM core_learner l
            JOIN core_student s ON l.student_id = s.sid
            WHERE s.email = %s
        """,
            [request.user.email],
        )
        learner = dictfetchone(cursor)

        # Fallback to first available learner if specific user isn't found
        if not learner:
            cursor.execute("SELECT student_id FROM core_learner LIMIT 1")
            learner = dictfetchone(cursor)

        learner_id = learner["student_id"] if learner else None

    if request.method == "POST":
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO core_booking (date, status, learner_id, tutor_id, slot_id)
                VALUES (%s, %s, %s, %s, %s)
            """,
                [
                    slot["date"],
                    "Confirmed",
                    learner_id,
                    slot["tutor_id"],
                    slot["id"],
                ],
            )
        return redirect("bookings")

    return render(request, "book_slot.html", {"slot": slot})