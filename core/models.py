from django.db import models


class Department(models.Model):
    dept_id = models.AutoField(primary_key=True)
    dept_name = models.CharField(max_length=100)

    def __str__(self):
        return self.dept_name


class Student(models.Model):
    sid = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    semester = models.IntegerField()

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name


class Tutor(models.Model):
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        primary_key=True
    )

    completed_sessions = models.IntegerField(default=0)
    avg_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0
    )

    tutor_status = models.CharField(max_length=20)

    def __str__(self):
        return self.student.name


class Learner(models.Model):
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        primary_key=True
    )

    learner_level = models.CharField(max_length=30)

    def __str__(self):
        return self.student.name


class Skill(models.Model):
    skill_id = models.AutoField(primary_key=True)
    skill_name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)

    def __str__(self):
        return self.skill_name


class AvailableSlot(models.Model):
    tutor = models.ForeignKey(
        Tutor,
        on_delete=models.CASCADE
    )

    slot_no = models.IntegerField()

    start_time = models.TimeField()
    end_time = models.TimeField()
    date = models.DateField()
    mode = models.CharField(max_length=20)

    class Meta:
        unique_together = ("tutor", "slot_no")

    def __str__(self):
        return f"{self.tutor} - Slot {self.slot_no}"


class Teaches(models.Model):
    tutor = models.ForeignKey(
        Tutor,
        on_delete=models.CASCADE
    )

    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("tutor", "skill")
        verbose_name_plural = "Teaches"

    def __str__(self):
        return f"{self.tutor} teaches {self.skill}"


class Learns(models.Model):
    learner = models.ForeignKey(
        Learner,
        on_delete=models.CASCADE
    )

    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("learner", "skill")
        verbose_name_plural = "Learns"

    def __str__(self):
        return f"{self.learner} learns {self.skill}"


class Badge(models.Model):
    badge_id = models.AutoField(primary_key=True)
    badge_name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.badge_name


class Earns(models.Model):
    tutor = models.ForeignKey(
        Tutor,
        on_delete=models.CASCADE
    )

    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE
    )

    date_earned = models.DateField()

    class Meta:
        unique_together = ("tutor", "badge")
        verbose_name_plural = "Earns"

    def __str__(self):
        return f"{self.tutor} earned {self.badge}"


class Booking(models.Model):
    booking_id = models.AutoField(primary_key=True)

    date = models.DateField()

    status = models.CharField(max_length=20)

    learner = models.ForeignKey(
        Learner,
        on_delete=models.CASCADE
    )

    tutor = models.ForeignKey(
        Tutor,
        on_delete=models.CASCADE
    )

    slot = models.ForeignKey(
        AvailableSlot,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"Booking {self.booking_id}"


class Ratings(models.Model):
    rating_id = models.AutoField(primary_key=True)

    rating = models.IntegerField()

    comment = models.TextField()

    warning = models.BooleanField(default=False)

    learner = models.ForeignKey(
        Learner,
        on_delete=models.CASCADE
    )

    tutor = models.ForeignKey(
        Tutor,
        on_delete=models.CASCADE
    )

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name_plural = "Ratings"

    def __str__(self):
        return f"Rating {self.rating}"