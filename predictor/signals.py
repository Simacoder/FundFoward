# predictor/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from predictor.models import Student, Donor
from predictor.matcher import Matcher

@receiver(post_save, sender=Student)
def generate_matches_for_student(sender, instance, created, **kwargs):
    """
    Run matching when a new student is created or updated.
    """
    matcher = Matcher(min_threshold=0.5)
    students = [instance]  # just this student
    donors = list(Donor.objects.all())
    for donor in donors:
        student_features = {
            "gpa": instance.gpa,
            "need_score": instance.need_score,
            "course": instance.course,
        }
        donor_features = {
            "min_gpa": donor.min_gpa,
            "preferred_course": donor.preferred_course,
            "donor_type": donor.donor_type,
            "max_amount": donor.max_amount,
        }
        score, explanation = matcher.score(student_features, donor_features)
        if score >= matcher.min_threshold:
            from predictor.models import Match
            Match.objects.update_or_create(
                student=instance,
                donor=donor,
                defaults={"score": score, "top_features": explanation}
            )


@receiver(post_save, sender=Donor)
def generate_matches_for_donor(sender, instance, created, **kwargs):
    """
    Run matching when a new donor is created or updated.
    """
    matcher = Matcher(min_threshold=0.5)
    donors = [instance]  # just this donor
    students = list(Student.objects.all())
    for student in students:
        student_features = {
            "gpa": student.gpa,
            "need_score": student.need_score,
            "course": student.course,
        }
        donor_features = {
            "min_gpa": instance.min_gpa,
            "preferred_course": instance.preferred_course,
            "donor_type": instance.donor_type,
            "max_amount": instance.max_amount,
        }
        score, explanation = matcher.score(student_features, donor_features)
        if score >= matcher.min_threshold:
            from predictor.models import Match
            Match.objects.update_or_create(
                student=student,
                donor=instance,
                defaults={"score": score, "top_features": explanation}
            )
