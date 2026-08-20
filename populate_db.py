import os
import django
from datetime import date, time

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Smart_Tutoring_System.settings")
django.setup()

from core.models import (
    Department, Student, Tutor, Learner, Skill,
    AvailableSlot, Teaches, Learns, Badge, Earns,
    Booking, Ratings
)

def populate():
    print("Populating database with expanded sample data...")

    # 1. Departments (4 Departments)
    depts_data = [
        "Computer Science & Engineering",
        "Electrical & Electronic Engineering",
        "Mechanical Engineering",
        "Business Administration"
    ]
    departments = []
    for d_name in depts_data:
        dept, _ = Department.objects.get_or_create(dept_name=d_name)
        departments.append(dept)

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
    for name, email, phone, sem, dept in students_info:
        s, _ = Student.objects.get_or_create(
            email=email,
            defaults={"name": name, "phone": phone, "semester": sem, "department": dept}
        )
        students.append(s)

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
    for st, sessions, rating, status in tutor_configs:
        t, _ = Tutor.objects.get_or_create(
            student=st,
            defaults={"completed_sessions": sessions, "avg_rating": rating, "tutor_status": status}
        )
        tutors.append(t)

    # 4. Learners (6 Learners)
    learners = []
    learner_levels = ["Beginner", "Intermediate", "Advanced", "Beginner", "Intermediate", "Advanced"]
    for idx, st in enumerate(students[6:]):
        l, _ = Learner.objects.get_or_create(
            student=st,
            defaults={"learner_level": learner_levels[idx]}
        )
        learners.append(l)

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
        sk, _ = Skill.objects.get_or_create(skill_name=s_name, category=cat)
        skills.append(sk)

    # 6. Teaches Relationships (6 rows)
    teaches_pairs = [
        (tutors[0], skills[0]), (tutors[0], skills[1]),
        (tutors[1], skills[5]), (tutors[2], skills[2]),
        (tutors[3], skills[3]), (tutors[5], skills[4]),
    ]
    for tut, sk in teaches_pairs:
        Teaches.objects.get_or_create(tutor=tut, skill=sk)

    # 7. Learns Relationships (6 rows)
    learns_pairs = [
        (learners[0], skills[0]), (learners[1], skills[1]),
        (learners[2], skills[2]), (learners[3], skills[3]),
        (learners[4], skills[4]), (learners[5], skills[5]),
    ]
    for lr, sk in learns_pairs:
        Learns.objects.get_or_create(learner=lr, skill=sk)

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
    for tut, num, st, et, d, mode in slot_configs:
        sl, _ = AvailableSlot.objects.get_or_create(
            tutor=tut, slot_no=num,
            defaults={"start_time": st, "end_time": et, "date": d, "mode": mode}
        )
        slots.append(sl)

    # 9. Badges (3 Badges)
    badges_data = [
        ("Top Rated Tutor", "Maintained an average rating above 4.8"),
        ("Session Master", "Completed more than 10 tutoring sessions"),
        ("Subject Expert", "Teaches more than 2 distinct subjects"),
    ]
    badges = []
    for b_name, desc in badges_data:
        bg, _ = Badge.objects.get_or_create(badge_name=b_name, description=desc)
        badges.append(bg)

    # 10. Earns (3 rows)
    Earns.objects.get_or_create(tutor=tutors[0], badge=badges[0], defaults={"date_earned": date(2026, 8, 10)})
    Earns.objects.get_or_create(tutor=tutors[0], badge=badges[1], defaults={"date_earned": date(2026, 8, 15)})
    Earns.objects.get_or_create(tutor=tutors[3], badge=badges[0], defaults={"date_earned": date(2026, 8, 18)})

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
    for lr, tut, sl, d, st in booking_configs:
        bk, _ = Booking.objects.get_or_create(
            learner=lr, tutor=tut, slot=sl,
            defaults={"date": d, "status": st}
        )
        bookings.append(bk)

    # 12. Ratings (3 Ratings)
    Ratings.objects.get_or_create(
        booking=bookings[0],
        defaults={"learner": learners[0], "tutor": tutors[0], "rating": 5, "comment": "Great session on Python basics!", "warning": False}
    )
    Ratings.objects.get_or_create(
        booking=bookings[1],
        defaults={"learner": learners[1], "tutor": tutors[0], "rating": 5, "comment": "Explained binary trees perfectly.", "warning": False}
    )
    Ratings.objects.get_or_create(
        booking=bookings[4],
        defaults={"learner": learners[4], "tutor": tutors[3], "rating": 4, "comment": "Good explanation of thermodynamics principles.", "warning": False}
    )

    print("Success! Database populated with 6 to 12 entries per table.")

if __name__ == "__main__":
    populate()