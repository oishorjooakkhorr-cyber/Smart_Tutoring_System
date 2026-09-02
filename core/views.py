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


import re


def login_view(request):
    # Check if custom student session is already active
    if "user_email" in request.session:
        return redirect("home")

    error = None
    if request.method == "POST":
        is_admin_login = request.POST.get("is_admin_login")

        if is_admin_login:
            admin_id = (request.POST.get("admin_id") or "").strip()
            password = (request.POST.get("password") or "").strip()

            if not admin_id or not password:
                error = "Admin ID and Password cannot be empty."
            elif admin_id == "cse370" and password == "cse370":
                request.session["user_email"] = "admin"
                request.session["user_name"] = "Administrator"
                request.session["role"] = "admin"
                return redirect("home")
            else:
                error = "Invalid Admin ID or password"
        else:
            email = (request.POST.get("email") or "").strip()
            password = request.POST.get("password") or ""

            if not email or not password:
                error = "Email and Password cannot be empty."
            else:
                # Query custom core_student table directly
                with connection.cursor() as cursor:
                    cursor.execute("SELECT sid, name, email, password FROM core_student WHERE email = %s", [email])
                    student = cursor.fetchone()

                    if student and student[3] == password:  # Validate email and password
                        request.session["user_sid"] = student[0]
                        request.session["user_name"] = student[1]
                        request.session["user_email"] = student[2]  # Store in session
                        request.session["role"] = "student"
                        
                        # Check if they are a learner
                        cursor.execute("SELECT 1 FROM core_learner WHERE student_id = %s", [student[0]])
                        request.session["is_learner"] = True if cursor.fetchone() else False
                        
                        # Check if they are a tutor
                        cursor.execute("SELECT 1 FROM core_tutor WHERE student_id = %s", [student[0]])
                        request.session["is_tutor"] = True if cursor.fetchone() else False
                        
                        return redirect("home")
                    else:
                        error = "Invalid student email or password"

    return render(request, "login.html", {"error": error})


def signup_view(request):
    error = None
    form_data = {
        "is_learner": True,
        "is_tutor": False
    }

    # Fetch departments dropdown list
    with connection.cursor() as cursor:
        cursor.execute("SELECT dept_id, dept_name FROM core_department;")
        departments = cursor.fetchall()

    if request.method == "POST":
        sid = (request.POST.get("sid") or "").strip()
        name = (request.POST.get("name") or "").strip()
        email = (request.POST.get("email") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        semester = (request.POST.get("semester") or "").strip()
        department_id = (request.POST.get("department_id") or "").strip()
        password = request.POST.get("password") or ""
        confirm_password = request.POST.get("confirm_password") or ""

        is_learner = bool(request.POST.get("is_learner"))
        is_tutor = bool(request.POST.get("is_tutor"))

        form_data = {
            "sid": sid,
            "name": name,
            "email": email,
            "phone": phone,
            "semester": semester,
            "department_id": department_id,
            "is_learner": is_learner,
            "is_tutor": is_tutor,
        }

        # 1. Required Fields Empty Check
        if not sid or not name or not email or not phone or not semester or not department_id or not password:
            error = "All fields are required and cannot be left blank."

        # 2. Role selection check
        elif not is_learner and not is_tutor:
            error = "Please select at least one role: Learner, Tutor, or both."

        # 3. Student ID (SID) length & character validation
        elif len(sid) < 4 or len(sid) > 20 or not sid.isalnum():
            error = "Student ID must be between 4 and 20 alphanumeric characters (letters/numbers only)."

        # 4. Full Name length validation
        elif len(name) < 2 or len(name) > 100:
            error = "Full name must be between 2 and 100 characters."

        # 5. Email format validation
        elif not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            error = "Please provide a valid email address (e.g., student@example.com)."

        # 6. Phone number format & length validation (10 to 15 digits)
        elif not re.match(r"^\+?[0-9]{10,15}$", phone):
            error = "Phone number must be between 10 and 15 digits (e.g. 01711111111)."

        # 7. Semester numeric range validation (1 to 16)
        elif not semester.isdigit() or int(semester) < 1 or int(semester) > 16:
            error = "Semester must be a valid number between 1 and 16."

        # 8. Password minimum length validation
        elif len(password) < 6:
            error = "Password is too short. It must be at least 6 characters long."

        # 9. Password confirmation match check
        elif confirm_password and password != confirm_password:
            error = "Passwords do not match. Please re-enter your password."

        else:
            with connection.cursor() as cursor:
                # Duplicate SID check
                cursor.execute("SELECT 1 FROM core_student WHERE sid = %s", [sid])
                if cursor.fetchone():
                    error = f"A student with ID '{sid}' is already registered."

                # Duplicate Email check
                if not error:
                    cursor.execute("SELECT 1 FROM core_student WHERE email = %s", [email])
                    if cursor.fetchone():
                        error = f"The email '{email}' is already in use by another account."

                # Duplicate Phone check
                if not error:
                    cursor.execute("SELECT 1 FROM core_student WHERE phone = %s", [phone])
                    if cursor.fetchone():
                        error = f"The phone number '{phone}' is already registered."

                # If all constraint checks pass, perform insertion
                if not error:
                    cursor.execute("""
                        INSERT INTO core_student (sid, name, email, phone, semester, department_id, password)
                        VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """, [sid, name, email, phone, int(semester), department_id, password])

                    if is_learner:
                        cursor.execute(
                            "INSERT INTO core_learner (student_id, learner_level) VALUES (%s, %s);", 
                            [sid, "Beginner"]
                        )

                    if is_tutor:
                        cursor.execute(
                            """
                            INSERT INTO core_tutor (student_id, completed_sessions, avg_rating, tutor_status) 
                            VALUES (%s, %s, %s, %s);
                            """, 
                            [sid, 0, 0.0, "Active"]
                        )

                    # AUTO-LOGIN: Store active user credentials in session
                    request.session["user_sid"] = sid
                    request.session["user_email"] = email
                    request.session["user_name"] = name
                    request.session["role"] = "student"
                    request.session["is_learner"] = is_learner
                    request.session["is_tutor"] = is_tutor

                    return redirect("home")

    return render(request, "signup.html", {
        "departments": departments,
        "error": error,
        "form_data": form_data
    })



def logout_view(request):
    request.session.flush()  # Clear custom user session
    logout(request)
    return redirect("login")


def home(request):
    if "user_email" not in request.session:
        return redirect("login")
    return render(request, "home.html", {
        "user_name": request.session.get("user_name", request.session.get("user_email")),
        "role": request.session.get("role"),
        "is_learner": request.session.get("is_learner", False),
        "is_tutor": request.session.get("is_tutor", False)
    })




def tutors(request):
    search_query = request.GET.get("q", "")
    status_filter = request.GET.get("status", "")
    skill_filter = request.GET.get("skill", "")
    min_rating = request.GET.get("min_rating", "")

    # Base SQL Query using Raw SQL
    sql = """
        SELECT DISTINCT t.student_id, t.completed_sessions, t.avg_rating, t.tutor_status, 
               s.name, s.email, s.phone, s.semester
        FROM core_tutor t
        JOIN core_student s ON t.student_id = s.sid
    """
    
    # If filtering by skill, we must join the teaches and skill tables
    if skill_filter:
        sql += """
            JOIN core_teaches teaches ON t.student_id = teaches.tutor_id
            JOIN core_skill sk ON teaches.skill_id = sk.skill_id
        """

    sql += " WHERE 1=1"
    params = []

    if search_query:
        sql += " AND s.name LIKE %s"
        params.append(f"%{search_query}%")

    if status_filter:
        sql += " AND t.tutor_status = %s"
        params.append(status_filter)

    if skill_filter:
        sql += " AND sk.skill_name = %s"
        params.append(skill_filter)
        
    if min_rating:
        sql += " AND t.avg_rating >= %s"
        params.append(min_rating)

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        data = dictfetchall(cursor)
        
        # Fetch all available skills for the dropdown menu
        cursor.execute("SELECT skill_name FROM core_skill ORDER BY skill_name")
        all_skills = [row[0] for row in cursor.fetchall()]


    for row in data:
        row["student"] = {"name": row["name"], "email": row["email"], "phone": row["phone"]}

    return render(
        request,
        "tutors.html",
        {
            "tutors": data,
            "search_query": search_query,
            "status_filter": status_filter,
            "skill_filter": skill_filter,
            "min_rating": min_rating,
            "all_skills": all_skills,
        },
    )



def learners(request):
    if request.session.get("role") != "admin":
        return redirect("home")

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
    active_email = request.session.get("user_email")
    active_sid = request.session.get("user_sid")
    role = request.session.get("role")

    if not active_email:
        return redirect("login")

    filter_tutor = request.GET.get("tutor_name", "").strip()
    filter_skill = request.GET.get("skill_name", "").strip()

    query = """
        SELECT slot.*, s.name AS student_name, sk.skill_name
        FROM core_availableslot slot
        JOIN core_tutor t ON slot.tutor_id = t.student_id
        JOIN core_student s ON t.student_id = s.sid
        LEFT JOIN core_skill sk ON slot.skill_id = sk.skill_id
        WHERE 1=1
    """
    params = []

    if role != "admin" and active_sid:
        query += " AND slot.tutor_id != %s"
        params.append(active_sid)

    if filter_tutor:
        query += " AND LOWER(s.name) LIKE LOWER(%s)"
        params.append(f"%%{filter_tutor}%%")

    if filter_skill:
        query += " AND LOWER(sk.skill_name) LIKE LOWER(%s)"
        params.append(f"%%{filter_skill}%%")

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        data = dictfetchall(cursor)

    for row in data:
        row["tutor"] = {"student": {"name": row["student_name"]}}
        row["skill_name_display"] = row["skill_name"] or "General / Unspecified"

    return render(request, "slots.html", {
        "slots": data,
        "filter_tutor": filter_tutor,
        "filter_skill": filter_skill
    })

def add_slot(request):
    if not request.session.get("is_tutor"):
        return redirect("home")
        
    tutor_id = request.session.get("user_sid")
    
    if request.method == "POST":
        slot_date = request.POST.get("slot_date")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")
        mode = request.POST.get("mode")
        skill_id = request.POST.get("skill_id")
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT MAX(slot_no) FROM core_availableslot WHERE tutor_id = %s", [tutor_id])
            max_slot = cursor.fetchone()[0]
            next_slot_no = (max_slot or 0) + 1
            
            cursor.execute("""
                INSERT INTO core_availableslot (tutor_id, slot_no, date, start_time, end_time, mode, skill_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, [tutor_id, next_slot_no, slot_date, start_time, end_time, mode, skill_id])
            
        return redirect("home")
        
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT s.skill_id, s.skill_name 
            FROM core_teaches t 
            JOIN core_skill s ON t.skill_id = s.skill_id 
            WHERE t.tutor_id = %s
        """, [tutor_id])
        my_skills = dictfetchall(cursor)
        
    return render(request, "add_slot.html", {"my_skills": my_skills})

def bookings(request):
    active_email = request.session.get("user_email")
    role = request.session.get("role")
    active_sid = request.session.get("user_sid")

    if not active_email:
        return redirect("login")

    filter_type = request.GET.get("type")  # "learner" or "tutor"

    query = """
        SELECT b.*, 
               ls.name AS learner_name, 
               ts.name AS tutor_name,
               COALESCE(slot.slot_no, 0) AS slot_no, 
               slot.start_time, 
               slot.end_time, 
               slot.mode,
               r.rating AS given_rating,
               r.comment AS given_comment
        FROM core_booking b
        JOIN core_learner l ON b.learner_id = l.student_id
        JOIN core_student ls ON l.student_id = ls.sid
        JOIN core_tutor t ON b.tutor_id = t.student_id
        JOIN core_student ts ON t.student_id = ts.sid
        LEFT JOIN core_availableslot slot ON b.slot_id = slot.id
        LEFT JOIN core_ratings r ON b.booking_id = r.booking_id
    """
    
    params = []
    where_clauses = []

    if role != "admin":
        if filter_type == "learner":
            where_clauses.append("b.learner_id = %s")
            params.append(active_sid)
        elif filter_type == "tutor":
            where_clauses.append("b.tutor_id = %s")
            params.append(active_sid)
        else:
            where_clauses.append("(b.learner_id = %s OR b.tutor_id = %s)")
            params.extend([active_sid, active_sid])
    else:
        if filter_type == "learner" and active_sid:
            where_clauses.append("b.learner_id = %s")
            params.append(active_sid)
        elif filter_type == "tutor" and active_sid:
            where_clauses.append("b.tutor_id = %s")
            params.append(active_sid)

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " ORDER BY b.booking_id DESC"

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        data = dictfetchall(cursor)

    from datetime import datetime, timedelta
    now = datetime.now()
    today_date = now.date()

    past_bookings = []
    ongoing_bookings = []
    upcoming_bookings = []

    for row in data:
        row["learner"] = {"student": {"name": row["learner_name"]}}
        row["tutor"] = {"student": {"name": row["tutor_name"]}}
        row["slot"] = {
            "slot_no": row["slot_no"],
            "start_time": row["start_time"],
            "end_time": row["end_time"],
            "mode": row["mode"],
        }
        row["can_rate"] = (role == "admin") or (active_sid and str(row["learner_id"]) == str(active_sid))
        row["is_tutor_of_session"] = bool(active_sid and str(row["tutor_id"]) == str(active_sid))
        
        row["can_cancel"] = False
        
        try:
            date_str = str(row["date"])
            time_str = str(row["start_time"])
            slot_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
            slot_d = slot_dt.date()
        except ValueError:
            try:
                slot_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                slot_d = slot_dt.date()
            except ValueError:
                slot_dt = None
                slot_d = None
                
        if row["status"] == "Confirmed" and slot_dt and (slot_dt - now > timedelta(hours=48)):
            row["can_cancel"] = True
            
        if row["status"] == "Cancelled" or row["status"] == "Completed" or (slot_d and slot_d < today_date):
            past_bookings.append(row)
        elif slot_d and slot_d == today_date:
            ongoing_bookings.append(row)
        else:
            upcoming_bookings.append(row)

    return render(
        request, 
        "bookings.html", 
        {
            "past_bookings": past_bookings,
            "ongoing_bookings": ongoing_bookings,
            "upcoming_bookings": upcoming_bookings,
            "role": role, 
            "filter_type": filter_type
        }
    )


def ratings(request):
    active_email = request.session.get("user_email")
    active_sid = request.session.get("user_sid")
    is_tutor = request.session.get("is_tutor", False)

    if not active_email:
        return redirect("login")

    query = """
        SELECT r.*, 
               ls.name AS learner_name, 
               ts.name AS tutor_name
        FROM core_ratings r
        JOIN core_learner l ON r.learner_id = l.student_id
        JOIN core_student ls ON l.student_id = ls.sid
        JOIN core_tutor t ON r.tutor_id = t.student_id
        JOIN core_student ts ON t.student_id = ts.sid
        ORDER BY r.rating_id DESC
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        data = dictfetchall(cursor)

    for row in data:
        row["learner"] = {"student": {"name": row["learner_name"]}}
        row["tutor"] = {"student": {"name": row["tutor_name"]}}

    # Filter ratings specifically received by the currently logged-in tutor
    portal = request.GET.get("portal", "")
    
    my_ratings = []
    if is_tutor and active_sid and portal != "learner":
        my_ratings = [r for r in data if str(r.get("tutor_id")) == str(active_sid)]
        
    is_learner = request.session.get("is_learner", False)
    my_given_ratings = []
    if is_learner and active_sid and portal != "tutor":
        my_given_ratings = [r for r in data if str(r.get("learner_id")) == str(active_sid)]

    return render(
        request, 
        "ratings.html", 
        {
            "ratings": data, 
            "my_ratings": my_ratings, 
            "my_given_ratings": my_given_ratings,
            "is_tutor": is_tutor,
            "is_learner": is_learner,
            "show_received": is_tutor and portal != "learner",
            "show_given": is_learner and portal != "tutor",
            "role": request.session.get("role")
        }
    )


def badges(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM core_badge")
        badges_data = dictfetchall(cursor)
        
        cursor.execute("""
            SELECT 
                ts.name, 
                t.completed_sessions, 
                t.avg_rating,
                CAST((t.completed_sessions * 10) + (t.avg_rating * 20) AS INT) AS points,
                (SELECT GROUP_CONCAT(b.badge_name, ', ') 
                 FROM core_earns e 
                 JOIN core_badge b ON e.badge_id = b.badge_id 
                 WHERE e.tutor_id = t.student_id) AS earned_badges
            FROM core_tutor t
            JOIN core_student ts ON t.student_id = ts.sid
            ORDER BY points DESC
        """)
        leaderboard = dictfetchall(cursor)
        for tutor in leaderboard:
            if tutor["earned_badges"]:
                tutor["earned_badges"] = tutor["earned_badges"].replace(",", ", ")

    return render(request, "badges.html", {"badges": badges_data, "leaderboard": leaderboard})


def book_slot(request, slot_id):
    active_email = request.session.get("user_email")
    active_sid = request.session.get("user_sid")

    if not active_email:
        return redirect("login")

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT slot.*, ts.name AS tutor_name 
            FROM core_availableslot slot
            JOIN core_tutor t ON slot.tutor_id = t.student_id
            JOIN core_student ts ON t.student_id = ts.sid
            WHERE slot.id = %s
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

    # Check if the user is attempting to book their own slot
    if (active_sid and str(slot["tutor_id"]) == str(active_sid)) or (learner_id and str(slot["tutor_id"]) == str(learner_id)):
        return render(request, "book_slot.html", {
            "slot": slot,
            "error": "You cannot book your own availability slot.",
            "is_self_slot": True
        })

    if request.method == "POST":
        with connection.cursor() as cursor:
            # CHECK 1: Is this slot already booked by someone else?
            cursor.execute(
                "SELECT COUNT(*) FROM core_booking WHERE slot_id = %s AND status != 'Cancelled'",
                [slot["id"]]
            )
            is_taken = cursor.fetchone()[0]

            if is_taken > 0:
                return render(request, "book_slot.html", {
                    "slot": slot, 
                    "error": "This slot has already been booked by another learner."
                })

            # CHECK 2: Does the learner already have a booking that overlaps with this time?
            cursor.execute(
                """
                SELECT COUNT(*) FROM core_booking b
                JOIN core_availableslot s ON b.slot_id = s.id
                WHERE b.learner_id = %s 
                  AND s.date = %s 
                  AND s.start_time < %s 
                  AND s.end_time > %s
                  AND b.status != 'Cancelled'
                """,
                [learner_id, str(slot["date"]), str(slot["end_time"]), str(slot["start_time"])]
            )
            has_conflict = cursor.fetchone()[0]

            if has_conflict > 0:
                return render(request, "book_slot.html", {
                    "slot": slot, 
                    "error": "You already have a confirmed booking that conflicts with this time."
                })

            # If no conflicts, insert the booking
            cursor.execute(
                """
                INSERT INTO core_booking (date, status, learner_id, tutor_id, slot_id)
                VALUES (%s, %s, %s, %s, %s)
            """,
                [
                    str(slot["date"]),
                    "Pending",
                    learner_id,
                    slot["tutor_id"],
                    slot["id"],
                ],
            )
        return redirect("bookings")

    return render(request, "book_slot.html", {"slot": slot})


def rate_booking(request, booking_id):
    active_email = request.session.get("user_email")
    active_sid = request.session.get("user_sid")
    role = request.session.get("role")

    if not active_email:
        return redirect("login")

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT b.*, ts.name AS tutor_name, ls.name AS learner_name
            FROM core_booking b
            JOIN core_tutor t ON b.tutor_id = t.student_id
            JOIN core_student ts ON t.student_id = ts.sid
            JOIN core_learner l ON b.learner_id = l.student_id
            JOIN core_student ls ON l.student_id = ls.sid
            WHERE b.booking_id = %s
            """,
            [booking_id],
        )
        booking = dictfetchone(cursor)

        if not booking:
            raise Http404("Booking does not exist")

    # LOGICAL & SECURITY CHECK:
    # A tutor cannot rate their own teaching session! Only the learner who attended (or admin) can rate.
    if role != "admin" and active_sid:
        if str(booking["tutor_id"]) == str(active_sid):
            return render(request, "rate_booking.html", {
                "booking": booking,
                "error": "Tutors cannot rate their own teaching sessions. Only learners who attended the session can submit ratings.",
                "cannot_rate": True
            })
        if str(booking["learner_id"]) != str(active_sid):
            return render(request, "rate_booking.html", {
                "booking": booking,
                "error": "You were not the learner for this session and cannot rate it.",
                "cannot_rate": True
            })

    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment", "")

        with connection.cursor() as cursor:
            cursor.execute("SELECT rating_id FROM core_ratings WHERE booking_id = %s", [booking_id])
            existing_rating = cursor.fetchone()

            if existing_rating:
                return render(request, "rate_booking.html", {
                    "booking": booking,
                    "error": "You have already submitted a rating for this session. Ratings cannot be changed once submitted.",
                    "cannot_rate": True
                })
            else:
                cursor.execute(
                    """
                    INSERT INTO core_ratings (rating, comment, warning, learner_id, tutor_id, booking_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    [rating, comment, False, booking["learner_id"], booking["tutor_id"], booking_id]
                )
            
            update_tutor_stats_and_badges(booking["tutor_id"])
        return redirect("ratings")

    return render(request, "rate_booking.html", {"booking": booking})

def warnings_view(request):
    if request.session.get("role") != "admin":
        return redirect("home")

    # Analytical Query: Find tutors where >70% of their ratings are < 3
    query = """
        SELECT 
            t.student_id,
            s.name AS reported_tutor_name,
            s.email AS tutor_email,
            COUNT(r.rating_id) AS total_ratings,
            SUM(CASE WHEN r.rating < 3 THEN 1 ELSE 0 END) AS bad_ratings,
            (SUM(CASE WHEN r.rating < 3 THEN 1 ELSE 0 END) * 100.0 / COUNT(r.rating_id)) AS bad_percentage
        FROM core_tutor t
        JOIN core_student s ON t.student_id = s.sid
        JOIN core_ratings r ON t.student_id = r.tutor_id
        GROUP BY t.student_id, s.name, s.email
        HAVING COUNT(r.rating_id) > 0 
           AND (SUM(CASE WHEN r.rating < 3 THEN 1 ELSE 0 END) * 100.0 / COUNT(r.rating_id)) >= 70
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        data = dictfetchall(cursor)

    return render(request, "warnings.html", {"warnings": data})
def delete_slot(request, slot_id):
    if request.session.get("role") != "admin":
        return redirect("home")
    
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM core_booking WHERE slot_id = %s", [slot_id])
        cursor.execute("DELETE FROM core_availableslot WHERE id = %s", [slot_id])
    
    return redirect("slots")

def delete_rating(request, rating_id):
    if request.session.get("role") != "admin":
        return redirect("home")
    
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM core_ratings WHERE rating_id = %s", [rating_id])
    
    return redirect("ratings")

def manage_skills(request):
    active_sid = request.session.get("user_sid")
    is_tutor = request.session.get("is_tutor", False)
    is_learner = request.session.get("is_learner", False)
    
    if not active_sid:
        return redirect("login")
        
    if request.method == "POST":
        action = request.POST.get("action")
        skill_id = request.POST.get("skill_id")
        new_skill_name = request.POST.get("new_skill_name", "").strip()
        new_skill_category = request.POST.get("new_skill_category", "General").strip()
        
        with connection.cursor() as cursor:
            if new_skill_name:
                cursor.execute("SELECT skill_id FROM core_skill WHERE LOWER(skill_name) = LOWER(%s)", [new_skill_name])
                existing = cursor.fetchone()
                if existing:
                    skill_id = existing[0]
                else:
                    cursor.execute("INSERT INTO core_skill (skill_name, category) VALUES (%s, %s)", [new_skill_name, new_skill_category])
                    skill_id = cursor.lastrowid
                    
            if not skill_id:
                return redirect("manage_skills")

            if action == "add_teach" and is_tutor:
                try:
                    cursor.execute("INSERT INTO core_teaches (tutor_id, skill_id) VALUES (%s, %s)", [active_sid, skill_id])
                except:
                    pass # Ignore unique constraint failures
            elif action == "remove_teach" and is_tutor:
                cursor.execute("DELETE FROM core_teaches WHERE tutor_id = %s AND skill_id = %s", [active_sid, skill_id])
            elif action == "add_learn" and is_learner:
                try:
                    cursor.execute("INSERT INTO core_learns (learner_id, skill_id) VALUES (%s, %s)", [active_sid, skill_id])
                except:
                    pass
            elif action == "remove_learn" and is_learner:
                cursor.execute("DELETE FROM core_learns WHERE learner_id = %s AND skill_id = %s", [active_sid, skill_id])
                
        return redirect("manage_skills")
        
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM core_skill ORDER BY skill_name")
        all_skills = dictfetchall(cursor)
        
        teaching_skills = []
        if is_tutor:
            cursor.execute('''
                SELECT s.* FROM core_skill s
                JOIN core_teaches t ON s.skill_id = t.skill_id
                WHERE t.tutor_id = %s
            ''', [active_sid])
            teaching_skills = dictfetchall(cursor)
            
        learning_skills = []
        if is_learner:
            cursor.execute('''
                SELECT s.* FROM core_skill s
                JOIN core_learns l ON s.skill_id = l.skill_id
                WHERE l.learner_id = %s
            ''', [active_sid])
            learning_skills = dictfetchall(cursor)
            
    return render(request, "manage_skills.html", {
        "all_skills": all_skills,
        "teaching_skills": teaching_skills,
        "learning_skills": learning_skills,
        "is_tutor": is_tutor,
        "is_learner": is_learner
    })

def upgrade_role(request):
    if request.method == "POST":
        active_sid = request.session.get("user_sid")
        if not active_sid:
            return redirect("login")
            
        new_role = request.POST.get("new_role")
        
        with connection.cursor() as cursor:
            if new_role == "tutor" and not request.session.get("is_tutor"):
                cursor.execute(
                    "INSERT INTO core_tutor (student_id, completed_sessions, avg_rating, tutor_status) VALUES (%s, 0, 0.0, 'Active')",
                    [active_sid]
                )
                request.session["is_tutor"] = True
                
            elif new_role == "learner" and not request.session.get("is_learner"):
                cursor.execute(
                    "INSERT INTO core_learner (student_id, learner_level) VALUES (%s, 'Beginner')",
                    [active_sid]
                )
                request.session["is_learner"] = True
                
    return redirect("home")


from datetime import date

def update_tutor_stats_and_badges(tutor_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*), AVG(rating) FROM core_ratings WHERE tutor_id = %s", [tutor_id])
        stats = cursor.fetchone()
        completed_sessions = stats[0] or 0
        avg_rating = stats[1] or 0.0
        
        cursor.execute(
            "UPDATE core_tutor SET completed_sessions = %s, avg_rating = %s WHERE student_id = %s",
            [completed_sessions, round(avg_rating, 2), tutor_id]
        )
        
        points = int((completed_sessions * 10) + (avg_rating * 20))
        
        cursor.execute("SELECT COUNT(*) FROM core_badge")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO core_badge (badge_name, description) VALUES ('Rising Star', '50+ Points')")
            cursor.execute("INSERT INTO core_badge (badge_name, description) VALUES ('Expert Tutor', '150+ Points')")
            cursor.execute("INSERT INTO core_badge (badge_name, description) VALUES ('Master Educator', '300+ Points')")
            
        cursor.execute("SELECT badge_id, badge_name FROM core_badge")
        all_badges = dictfetchall(cursor)
        
        for badge in all_badges:
            award = False
            if badge["badge_name"] == "Rising Star" and points >= 50:
                award = True
            elif badge["badge_name"] == "Expert Tutor" and points >= 150:
                award = True
            elif badge["badge_name"] == "Master Educator" and points >= 300:
                award = True
                
            if award:
                cursor.execute("SELECT 1 FROM core_earns WHERE tutor_id = %s AND badge_id = %s", [tutor_id, badge["badge_id"]])
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO core_earns (tutor_id, badge_id, date_earned) VALUES (%s, %s, %s)",
                        [tutor_id, badge["badge_id"], str(date.today())]
                    )

def confirm_booking(request, booking_id):
    active_sid = request.session.get("user_sid")
    if not active_sid:
        return redirect("login")
    
    with connection.cursor() as cursor:
        # Check if the booking belongs to this tutor
        cursor.execute("SELECT tutor_id FROM core_booking WHERE booking_id = %s", [booking_id])
        booking = cursor.fetchone()
        if booking and str(booking[0]) == str(active_sid):
            cursor.execute("UPDATE core_booking SET status = 'Confirmed' WHERE booking_id = %s", [booking_id])
            
    return redirect("bookings")

from datetime import datetime, timedelta

def cancel_booking(request, booking_id):
    active_sid = request.session.get("user_sid")
    if not active_sid:
        return redirect("login")
        
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT b.learner_id, b.tutor_id, s.date, s.start_time, b.status 
            FROM core_booking b
            JOIN core_availableslot s ON b.slot_id = s.id
            WHERE b.booking_id = %s
        """, [booking_id])
        booking = cursor.fetchone()
        
        if booking:
            learner_id, tutor_id, slot_date, slot_time, status = booking
            
            # Allow cancellation only if they are the learner or tutor
            if str(active_sid) in [str(learner_id), str(tutor_id)] and status == 'Confirmed':
                try:
                    # Parse the slot datetime
                    date_str = str(slot_date)
                    time_str = str(slot_time)
                    slot_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        slot_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                    except ValueError:
                        slot_dt = None
                        
                if slot_dt:
                    now = datetime.now()
                    # Check if it's more than 48 hours away
                    if slot_dt - now > timedelta(hours=48):
                        cursor.execute("UPDATE core_booking SET status = 'Cancelled' WHERE booking_id = %s", [booking_id])
                        
    return redirect("bookings")

def reject_booking(request, booking_id):
    active_sid = request.session.get("user_sid")
    if not active_sid:
        return redirect("login")
    
    with connection.cursor() as cursor:
        # Check if the booking belongs to this tutor
        cursor.execute("SELECT tutor_id FROM core_booking WHERE booking_id = %s", [booking_id])
        booking = cursor.fetchone()
        if booking and str(booking[0]) == str(active_sid):
            cursor.execute("UPDATE core_booking SET status = 'Cancelled' WHERE booking_id = %s", [booking_id])
            
    return redirect("bookings")



