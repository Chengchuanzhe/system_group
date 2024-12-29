from django.contrib import admin
from app01.models import UserProfile
from app01.models import Task
from app01.models import Homework
from app01.models import Course
# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Task)
admin.site.register(Homework)
admin.site.register(Course)