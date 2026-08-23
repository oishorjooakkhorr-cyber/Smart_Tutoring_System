from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout
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
    # Check if custom student session is already active
    if "user_email" in request.session:
        return redirect("home")

    error = None
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Query custom core_student table directly
        with connection.cursor() as cursor:
            cursor.execute("SELECT email, password FROM core_student WHERE email = %s", [email])
            student = cursor.fetchone()

        if student and student[1] == password:  # Validate email and password
            request.session["user_email"] = student[0]  # Store in session
            return redirect("home")
        else:
            error = "Invalid email or password"

    return render(request, "login.html", {"error": error})



from django.shortcuts import render, redirect
from django.db import connection

def dictfetchall(cursor):
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def signup_view(request):
    if request.method == "POST":
        sid = request.POST.get("sid")
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        semester = request.POST.get("semester")
        department_id = request.POST.get("department_id")
        password = request.POST.get("password")

        is_learner = request.POST.get("is_learner")
        is_tutor = request.POST.get("is_tutor")

        slot_date = request.POST.get("slot_date")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")
        mode = request.POST.get("mode")

        with connection.cursor() as cursor:
            # 1. Insert into core_student
            cursor.execute("""
                INSERT INTO core_student (sid, name, email, phone, semester, department_id, password)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, [sid, name, email, phone, semester, department_id, password])

            # 2. Add to core_learner if checked
            if is_learner:
                cursor.execute(
                    "INSERT INTO core_learner (student_id, learner_level) VALUES (%s, %s);", 
                    [sid, "Beginner"]
                )

            # 3. Add to core_tutor and post initial slot if checked
            if is_tutor:
                cursor.execute(
                    """
                    INSERT INTO core_tutor (student_id, completed_sessions, avg_rating, tutor_status) 
                    VALUES (%s, %s, %s, %s);
                    """, 
                    [sid, 0, 0.0, "Active"]
                )

                if slot_date and start_time and end_time:
                    cursor.execute("""
                        INSERT INTO core_availableslot (tutor_id, date, start_time, end_time, mode)
                        VALUES (%s, %s, %s, %s, %s);
                    """, [sid, slot_date, start_time, end_time, mode])

        # AUTO-LOGIN: Store active user credentials in session
        request.session["user_email"] = email
        request.session["user_name"] = name

        # Redirect straight into the app home page
        return redirect("home")

    # Fetch departments dropdown list
    with connection.cursor() as cursor:
        cursor.execute("SELECT dept_id, dept_name FROM core_department;")
        departments = cursor.fetchall()

    return render(request, "signup.html", {"departments": departments})



def logout_view(request):
    request.session.flush()  # Clear custom user session
    logout(request)
    return redirect("login")


def home(request):
    return render(request, "home.html")


def students(request):
    # Enforce session check
    if "user_email" not in request.session:
        return redirect("login")

    # Joined ON s.department_id = d.dept_id
    query = """
        SELECT s.sid, s.name, s.email, s.phone, s.semester, s.password, d.dept_name 
        FROM core_student s
        JOIN core_department d ON s.department_id = d.dept_id;
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        data = dictfetchall(cursor)

    # Reconstruct nested structure for template rendering
    for row in data:
        row["department"] = {"dept_name": row["dept_name"]}

    return render(request, "students.html", {"students": data})


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


def skills(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM core_skill")
        data = dictfetchall(cursor)

    return render(request, "skills.html", {"skills": data})


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


def bookings(request):
    query = """
        SELECT b.*, 
               ls.name AS learner_name, 
               ts.name AS tutor_name,
               COALESCE(slot.slot_no, 0) AS slot_no, 
               slot.start_time, 
               slot.end_time, 
               slot.mode
        FROM core_booking b
        JOIN core_learner l ON b.learner_id = l.student_id
        JOIN core_student ls ON l.student_id = ls.sid
        JOIN core_tutor t ON b.tutor_id = t.student_id
        JOIN core_student ts ON t.student_id = ts.sid
        LEFT JOIN core_availableslot slot ON b.slot_id = slot.id
        ORDER BY b.booking_id ASC;
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


def badges(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM core_badge")
        data = dictfetchall(cursor)

    return render(request, "badges.html", {"badges": data})


def book_slot(request, slot_id):
    active_email = request.session.get("user_email")

    with connection.cursor() as cursor:
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

        cursor.execute(
            """
            SELECT l.student_id 
            FROM core_learner l
            JOIN core_student s ON l.student_id = s.sid
            WHERE s.email = %s
        """,
            [active_email],
        )
        learner = dictfetchone(cursor)

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


def rate_booking(request, booking_id):
    active_email = request.session.get("user_email")
    if not active_email:
        return redirect("login")

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT b.*
            FROM core_booking b
            WHERE b.booking_id = %s
            """,
            [booking_id],
        )
        booking = dictfetchone(cursor)

        if not booking:
            raise Http404("Booking does not exist")

    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment", "")

        with connection.cursor() as cursor:
            cursor.execute("SELECT rating_id FROM core_ratings WHERE booking_id = %s", [booking_id])
            existing_rating = cursor.fetchone()

            if existing_rating:
                cursor.execute(
                    """
                    UPDATE core_ratings 
                    SET rating = %s, comment = %s 
                    WHERE booking_id = %s
                    """,
                    [rating, comment, booking_id]
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO core_ratings (rating, comment, warning, learner_id, tutor_id, booking_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    [rating, comment, False, booking["learner_id"], booking["tutor_id"], booking_id]
                )
        return redirect("ratings")

    return render(request, "rate_booking.html", {"booking": booking})