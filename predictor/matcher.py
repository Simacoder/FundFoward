# predictor/matcher.py
from predictor.models import Student, Donor, Match

class Matcher:
    """
    Matcher class to score student–donor compatibility and store matches.
    """

    def __init__(self, min_threshold=0.5):
        """
        min_threshold: Minimum score required to save a match (0-1).
        """
        self.min_threshold = min_threshold

    def score(self, student_features, donor_features):
        """
        Improved scoring function with transparency.
        Returns (score, explanation)
        """
        explanation = {}
        score = 0.0

        # GPA contribution
        gpa = student_features.get("gpa", 0) or 0
        min_gpa = donor_features.get("min_gpa", 0) or 0
        if gpa >= min_gpa:
            normalized_gpa = min(gpa / 4.0, 1.0)
            gpa_score = 0.4 * normalized_gpa
            score += gpa_score
            explanation["gpa_match"] = round(gpa_score, 3)

        # Course match
        preferred_course = (donor_features.get("preferred_course") or "Any").lower()
        student_course = (student_features.get("course") or "").lower()
        if preferred_course == "any" or preferred_course in student_course:
            score += 0.4
            explanation["course_match"] = 0.4

        # Need score contribution (scaled 0-1)
        need_score = min(student_features.get("need_score", 0) or 0, 100) / 100
        need_score_contrib = 0.2 * need_score
        score += need_score_contrib
        explanation["need_score"] = round(need_score_contrib, 3)

        final_score = round(min(score, 1.0), 3)
        return final_score, explanation

    def generate_for_all(self):
        """
        Generate matches for all students and donors, store them in DB.
        """
        Match.objects.all().delete()  # optional: clear old matches
        total_matches = 0

        students = Student.objects.all()
        donors = Donor.objects.all()

        for student in students:
            student_features = {
                "gpa": student.gpa,
                "need_score": student.need_score,
                "course": student.course,
            }

            for donor in donors:
                donor_features = {
                    "min_gpa": donor.min_gpa,
                    "preferred_course": donor.preferred_course,
                    "donor_type": donor.donor_type,
                    "max_amount": donor.max_amount,
                }
                s, explanation = self.score(student_features, donor_features)
                if s >= self.min_threshold:
                    Match.objects.update_or_create(
                        student=student,
                        donor=donor,
                        defaults={"score": s, "top_features": explanation}
                    )
                    total_matches += 1

        return total_matches


# Convenience function if you just want scoring without instantiating Matcher
def score(student_features, donor_features):
    return Matcher().score(student_features, donor_features)
