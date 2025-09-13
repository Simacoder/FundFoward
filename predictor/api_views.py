# predictor/api_views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Student, Donor, BursaryRequest, Transaction
from .matcher import score as match_donor  # your ML match function
import json

@csrf_exempt
def match_score(request):
    """
    POST: { "student_id": 1, "donor_id": 2 }
    Returns: { "match_score": 0.87 }
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            student = Student.objects.get(id=data["student_id"])
            donor = Donor.objects.get(id=data["donor_id"])

            student_features = {
                "gpa": student.gpa,
                "course": student.course,
                "need_score": student.need_score,
            }
            donor_features = {
                "donor_type": donor.donor_type,
                "preferred_course": donor.preferred_course,
            }
            score = match_donor(student_features, donor_features)
            return JsonResponse({"match_score": round(float(score), 3)})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid method"}, status=405)


@csrf_exempt
def fund_student(request):
    """
    POST: { "bursary_id": 10, "donor_id": 2, "amount": 500 }
    Simulates a donor funding a bursary request and marks it as funded.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            bursary = BursaryRequest.objects.get(id=data["bursary_id"])
            donor = Donor.objects.get(id=data["donor_id"])

            # Simple mock payment simulation
            bursary.amount_funded += data["amount"]
            bursary.save()

            Transaction.objects.create(
                bursary_request=bursary,
                donor=donor,
                amount=data["amount"],
                status="SUCCESS"
            )

            return JsonResponse({
                "status": "success",
                "message": f"{data['amount']} funded successfully",
                "bursary_status": "fully funded" if bursary.is_fully_funded() else "pending"
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid method"}, status=405)


def registration_alerts(request):
    """
    GET: Returns list of students with unpaid registration fees (for queue reduction).
    """
    unpaid_students = Student.objects.filter(registration_paid=False)
    results = [
        {
            "id": s.id,
            "name": s.name,
            "course": s.course,
            "gpa": s.gpa,
            "need_score": s.need_score,
        }
        for s in unpaid_students
    ]
    return JsonResponse({"unpaid_students": results})
