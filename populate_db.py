import os
import django
from datetime import date, time

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Smart_Tutoring_System.settings")
django.setup()

from django.db import connection


def get_or_create_sql(cursor, table, match_col, match_val, insert_cols, insert_vals):
    """Helper function to replicate get_or_create behavior using Raw SQL."""
    select_query = f"SELECT id FROM {table} WHERE {match_col} = %s;"
    if match_col in ["dept_id", "sid", "skill_id", "badge_id", "booking_id", "rating_id"]:
        select_query = f"SELECT {match_col} FROM {table} WHERE {match_col} = %s;"

    cursor.execute(select_query, [match_val])
    row = cursor.fetchone()

    if row:
        return row[0]
    else:
        cols_str = ", ".join(insert_cols)
        placeholders = ", ".join(["%s"] * len(insert_vals))
        insert_query = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders});"
        cursor.execute(insert_query, insert_vals)
        return cursor.lastrowid


def populate():
    print("Populating database with expanded sample data using Raw SQL...")

    with connection.cursor() as cursor:
        # 1. Departments (4 Departments)
        depts_data = [
            "Computer Science & Engineering",
            "Electrical & Electronic Engineering",
            "Mechanical Engineering",
            "Business Administration",
        ]
        departments = []
        for d_name in depts_data:
            d_id = get_or_create_sql(
                cursor, "core_department", "dept_name", d_name, ["dept_name"], [d_name]
            )
            departments.append(d_id)

        # 2. Students (12 Students)
        students_info = [
            ("Alice Smith", "alice@example.com", "01711111111", 5, departments[0]),
            ("Bob Johnson", "bob@example.com", "01822222222", 6, departments[0]),
            ("Charlie Brown", "charlie@example.com", "01933333333", 3, departments[1]),
            ("Diana Prince", "diana@example.com", "01644444444", 4, departments[1]),
            ("Evan Wright", "evan@example.com", "01555555555", 7, departments[2]),
            ("Fiona Gallagher", "fiona@example.com", "01766666666", 2, departments[3]),
            ("George Clark", "george@example.com", "01877777777", 8, departments[0]),
            ("Hannah Abbott", "hannah@example.com", "01988888888", 1, departments[0]),
            ("Ian Malcolm", "ian@example.com", "01699999999", 5, departments[2]),
            ("Julia Roberts", "julia@example.com", "01500000000", 6, departments[3]),
            ("Kevin Bacon", "kevin@example.com", "01712345678", 4, departments[1]),
            ("Laura Croft", "laura@example.com", "01887654321", 3, departments[0]),
        ]

        students = []
        for name, email, phone, sem, dept_id in students_info:
            cursor.execute("SELECT sid FROM core_student WHERE email = %s;", [email])
            row = cursor.fetchone()
            if row:
                s_id = row[0]
            else:
                cursor.execute(
                    """
                    INSERT INTO core_student (name, email, phone, semester, department_id)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    [name, email, phone, sem, dept_id],
                )
                s_id = cursor.lastrowid
            students.append(s_id)

        # 3. Tutors (6 Tutors)
        tutors = []
        tutor_configs = [
            (students[0], 15, 4.90, "Active"),
            (students[1], 10, 4.65, "Active"),
            (students[2], 8, 4.40, "Active"),
            (students[3], 20, 4.95, "Active"),
            (students[4], 5, 4.20, "Inactive"),
            (students[5], 12, 4.80, "Active"),
        ]
        for st_id, sessions, rating, status in tutor_configs:
            cursor.execute("SELECT student_id FROM core_tutor WHERE student_id = %s;", [st_id])
            row = cursor.fetchone()
            if row:
                t_id = row[0]
            else:
                cursor.execute(
                    """
                    INSERT INTO core_tutor (student_id, completed_sessions, avg_rating, tutor_status)
                    VALUES (%s, %s, %s, %s);
                    """,
                    [st_id, sessions, rating, status],
                )
                t_id = st_id
            tutors.append(t_id)

        # 4. Learners (6 Learners)
        learners = []
        learner_levels = ["Beginner", "Intermediate", "Advanced", "Beginner", "Intermediate", "Advanced"]
        for idx, st_id in enumerate(students[6:]):
            cursor.execute("SELECT student_id FROM core_learner WHERE student_id = %s;", [st_id])
            row = cursor.fetchone()
            if row:
                l_id = row[0]
            else:
                cursor.execute(
                    """
                    INSERT INTO core_learner (student_id, learner_level)
                    VALUES (%s, %s);
                    """,
                    [st_id, learner_levels[idx]],
                )
                l_id = st_id
            learners.append(l_id)

        # 5. Skills (6 Skills)
        skills_data = [
            ("Python Programming", "Computer Science"),
            ("Data Structures", "Computer Science"),
            ("Circuit Analysis", "Engineering"),
            ("Thermodynamics", "Engineering"),
            ("Financial Accounting", "Business"),
            ("Database Systems", "Computer Science"),
        ]
        skills = []
        for s_name, cat in skills_data:
            cursor.execute("SELECT skill_id FROM core_skill WHERE skill_name = %s AND category = %s;", [s_name, cat])
            row = cursor.fetchone()
            if row:
                sk_id = row[0]
            else:
                cursor.execute(
                    "INSERT INTO core_skill (skill_name, category) VALUES (%s, %s);",
                    [s_name, cat],
                )
                sk_id = cursor.lastrowid
            skills.append(sk_id)

        # 6. Teaches Relationships (6 rows)
        teaches_pairs = [
            (tutors[0], skills[0]), (tutors[0], skills[1]),
            (tutors[1], skills[5]), (tutors[2], skills[2]),
            (tutors[3], skills[3]), (tutors[5], skills[4]),
        ]
        for tut_id, sk_id in teaches_pairs:
            cursor.execute("SELECT id FROM core_teaches WHERE tutor_id = %s AND skill_id = %s;", [tut_id, sk_id])
            if not cursor.fetchone():
                cursor.execute("INSERT INTO core_teaches (tutor_id, skill_id) VALUES (%s, %s);", [tut_id, sk_id])

        # 7. Learns Relationships (6 rows)
        learns_pairs = [
            (learners[0], skills[0]), (learners[1], skills[1]),
            (learners[2], skills[2]), (learners[3], skills[3]),
            (learners[4], skills[4]), (learners[5], skills[5]),
        ]
        for lr_id, sk_id in learns_pairs:
            cursor.execute("SELECT id FROM core_learns WHERE learner_id = %s AND skill_id = %s;", [lr_id, sk_id])
            if not cursor.fetchone():
                cursor.execute("INSERT INTO core_learns (learner_id, skill_id) VALUES (%s, %s);", [lr_id, sk_id])

        # 8. Available Slots (6 Slots)
        slots = []
        slot_configs = [
            (tutors[0], 101, time(9, 0), time(10, 0), date(2026, 9, 1), "Online"),
            (tutors[0], 102, time(10, 30), time(11, 30), date(2026, 9, 1), "Online"),
            (tutors[1], 103, time(14, 0), time(15, 0), date(2026, 9, 2), "In-Person"),
            (tutors[2], 104, time(11, 0), time(12, 0), date(2026, 9, 3), "Online"),
            (tutors[3], 105, time(15, 0), time(16, 0), date(2026, 9, 4), "In-Person"),
            (tutors[5], 106, time(16, 30), time(17, 30), date(2026, 9, 5), "Online"),
        ]
        for tut_id, num, st, et, d, mode in slot_configs:
            cursor.execute("SELECT id FROM core_availableslot WHERE tutor_id = %s AND slot_no = %s;", [tut_id, num])
            row = cursor.fetchone()
            if row:
                sl_id = row[0]
            else:
                cursor.execute(
                    """
                    INSERT INTO core_availableslot (tutor_id, slot_no, start_time, end_time, date, mode)
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """,
                    [tut_id, num, st, et, d, mode],
                )
                sl_id = cursor.lastrowid
            slots.append(sl_id)

        # 9. Badges (3 Badges)
        badges_data = [
            ("Top Rated Tutor", "Maintained an average rating above 4.8"),
            ("Session Master", "Completed more than 10 tutoring sessions"),
            ("Subject Expert", "Teaches more than 2 distinct subjects"),
        ]
        badges = []
        for b_name, desc in badges_data:
            cursor.execute("SELECT badge_id FROM core_badge WHERE badge_name = %s;", [b_name])
            row = cursor.fetchone()
            if row:
                bg_id = row[0]
            else:
                cursor.execute("INSERT INTO core_badge (badge_name, description) VALUES (%s, %s);", [b_name, desc])
                bg_id = cursor.lastrowid
            badges.append(bg_id)

        # 10. Earns (3 rows)
        earns_configs = [
            (tutors[0], badges[0], date(2026, 8, 10)),
            (tutors[0], badges[1], date(2026, 8, 15)),
            (tutors[3], badges[0], date(2026, 8, 18)),
        ]
        for tut_id, bg_id, d_earned in earns_configs:
            cursor.execute("SELECT id FROM core_earns WHERE tutor_id = %s AND badge_id = %s;", [tut_id, bg_id])
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO core_earns (tutor_id, badge_id, date_earned) VALUES (%s, %s, %s);",
                    [tut_id, bg_id, d_earned],
                )

        # 11. Bookings (6 Bookings)
        bookings = []
        booking_configs = [
            (learners[0], tutors[0], slots[0], date(2026, 9, 1), "Completed"),
            (learners[1], tutors[0], slots[1], date(2026, 9, 1), "Completed"),
            (learners[2], tutors[1], slots[2], date(2026, 9, 2), "Confirmed"),
            (learners[3], tutors[2], slots[3], date(2026, 9, 3), "Pending"),
            (learners[4], tutors[3], slots[4], date(2026, 9, 4), "Completed"),
            (learners[5], tutors[5], slots[5], date(2026, 9, 5), "Confirmed"),
        ]
        for lr_id, tut_id, sl_id, d, st in booking_configs:
            cursor.execute(
                "SELECT booking_id FROM core_booking WHERE learner_id = %s AND tutor_id = %s AND slot_id = %s;",
                [lr_id, tut_id, sl_id],
            )
            row = cursor.fetchone()
            if row:
                bk_id = row[0]
            else:
                cursor.execute(
                    """
                    INSERT INTO core_booking (learner_id, tutor_id, slot_id, date, status)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    [lr_id, tut_id, sl_id, d, st],
                )
                bk_id = cursor.lastrowid
            bookings.append(bk_id)

        # 12. Ratings (3 Ratings)
        ratings_configs = [
            (bookings[0], learners[0], tutors[0], 5, "Great session on Python basics!", False),
            (bookings[1], learners[1], tutors[0], 5, "Explained binary trees perfectly.", False),
            (bookings[4], learners[4], tutors[3], 4, "Good explanation of thermodynamics principles.", False),
        ]
        for bk_id, lr_id, tut_id, rating_val, comment, warning in ratings_configs:
            cursor.execute("SELECT rating_id FROM core_ratings WHERE booking_id = %s;", [bk_id])
            if not cursor.fetchone():
                cursor.execute(
                    """
                    INSERT INTO core_ratings (booking_id, learner_id, tutor_id, rating, comment, warning)
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """,
                    [bk_id, lr_id, tut_id, rating_val, comment, warning],
                )

    print("Success! Database populated with 6 to 12 entries per table using Raw SQL.")


if __name__ == "__main__":
    populate()