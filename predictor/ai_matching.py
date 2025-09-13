# predictor/ai_matching.py
from .models import Student, Donor

def match_donors_to_students(donor):
    """
    Returns top 5 students matching donor preferences:
    - GPA >= donor.min_gpa
    - Course in donor.preferred_course
    - Highest need_score
    """
    students = Student.objects.filter(
        gpa__gte=donor.min_gpa,
        course__in=donor.preferred_course.split(",")  
    ).order_by("-need_score")[:5]
    return students
