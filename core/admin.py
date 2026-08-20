from django.contrib import admin

from django.contrib import admin
from .models import (
    Department,
    Student,
    Tutor,
    Learner,
    Skill,
    AvailableSlot,
    Teaches,
    Learns,
    Badge,
    Earns,
    Booking,
    Ratings,
)

admin.site.register(Department)
admin.site.register(Student)
admin.site.register(Tutor)
admin.site.register(Learner)
admin.site.register(Skill)
admin.site.register(AvailableSlot)
admin.site.register(Teaches)
admin.site.register(Learns)
admin.site.register(Badge)
admin.site.register(Earns)
admin.site.register(Booking)
admin.site.register(Ratings)
