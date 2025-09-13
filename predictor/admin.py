# predictor/admin.py
from django.contrib import admin
from .models import Student, Donor, UniversityPayment

admin.site.register(Student)
admin.site.register(Donor)
admin.site.register(UniversityPayment)