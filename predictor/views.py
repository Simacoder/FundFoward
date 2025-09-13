# predictor/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib import messages
from django.contrib.auth.views import LogoutView
from django.contrib.auth import logout
from django.shortcuts import render
from .forms import WalletTopUpForm
from .forms import TopUpForm, FundStudentForm
from .forms import DonorRegistrationForm, StudentRegistrationForm
from .ai_matching import match_donors_to_students
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from decimal import Decimal



from .models import (
    Student, Donor, BursaryRequest, Match, Transaction,
    RegistrationFlag, AcademicRecord, AccessRequest, UniversityPayment
)
from .forms import (
    StudentRegistrationForm, DonorRegistrationForm,
    BursaryRequestForm, AcademicUploadForm
)
from .matcher import score as matcher_score  # simple ML/heuristic function

# -----------------------
# Helper role checks
# -----------------------
def is_donor(user):
    return hasattr(user, "donor")

def is_student(user):
    return hasattr(user, "student")



# -----------------------
# Home
# -----------------------
def home(request):
    """
    Home landing. If logged-in donor, show wallet balance for convenience.
    """
    context = {}
    if request.user.is_authenticated and is_donor(request.user):
        context['donor'] = request.user.donor
    return render(request, "predictor/home.html", context)



def services(request):
    return render(request, 'predictor/services.html')

def about_view(request):
    return render(request, "predictor/about.html")


def donor_logout(request):
    if request.user.is_authenticated and hasattr(request.user, "donor"):
        logout(request)
        messages.success(request, "You have been logged out successfully.")
        return render(request, "predictor/donor_logged_out.html")
    else:
        return redirect("login")  # if not a donor, send to login


# -----------------------
# Registration (Student / Donor)
# -----------------------
def student_register(request):
    """
    Creates a Django User and a Student record using email as username.
    """
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password1")  # ensure your form has password1 field
            if not email or not password:
                messages.error(request, "Email and password are required.")
                return render(request, "predictor/student_register.html", {"form": form})
            
            # create Django user
            user = User.objects.create_user(username=email, email=email, password=password)
            
            # create Student object
            student = form.save(commit=False)
            student.user = user
            student.save()
            
            # create a sample registration flag (simulation)
            RegistrationFlag.objects.create(
                student=student,
                semester="2025S2",
                is_paid=False,
                flagged=True,
                flagged_reason="Unpaid registration fee"
            )
            
            messages.success(request, "Student account created. Please log in.")
            return redirect("login")
    else:
        form = StudentRegistrationForm()
    
    return render(request, "predictor/student_register.html", {"form": form})


def donor_register(request):
    if request.method == "POST":
        form = DonorRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")

            if not email:
                messages.error(request, "Email is required.")
                return render(request, "predictor/donor_register.html", {"form": form})

            username = email  # Ensure username is set
            user = User.objects.create_user(username=username, email=email, password=password)

            donor = form.save(commit=False)
            donor.user = user
            donor.save()

            messages.success(request, "Donor account created. Please log in.")
            return redirect("login")
    else:
        form = DonorRegistrationForm()
    return render(request, "predictor/donor_register.html", {"form": form})

class DonorLoginView(LoginView):
    template_name = "predictor/donor_login.html"

    def get_success_url(self):
        # Redirect donors to their dashboard automatically
        if hasattr(self.request.user, "donor"):
            return reverse_lazy("donor_dashboard")
        return reverse_lazy("home")
# ------------------------------
# Student requests bursary
@login_required
@user_passes_test(is_student)
def request_fee(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.user.student.id != student.id:
        return HttpResponseForbidden("You cannot access other students' requests.")
    
    if request.method == "POST":
        form = BursaryRequestForm(request.POST)
        if form.is_valid():
            br = form.save(commit=False)
            br.student = student
            br.save()
            
            # Match donors
            donors = Donor.objects.all()
            results = []
            for d in donors:
                s = {'gpa': student.gpa, 'need_score': student.need_score, 'course': student.course}
                donor_info = {
                    'donor_type': d.donor_type,
                    'preferred_course': d.preferred_course or 'Any',
                    'min_gpa': d.min_gpa,
                    'max_amount': float(d.max_amount)
                }
                score = matcher_score(s, donor_info)
                results.append({'donor': d, 'score': score})
            results = sorted(results, key=lambda x: x['score'], reverse=True)[:10]

            # Save matches
            for r in results:
                Match.objects.create(student=student, donor=r['donor'], score=r['score'])

            return render(request, 'predictor/match_result.html', {'results': results, 'student': student})
    else:
        form = BursaryRequestForm()

    return render(request, 'predictor/request_fee.html', {'form': form, 'student': student})

# -----------------------
# Donor dashboard & wallet
# -----------------------
@login_required
@user_passes_test(lambda u: hasattr(u, "donor"))
def donor_dashboard(request):
    donor = get_object_or_404(Donor, user=request.user)

    # ---------- Wallet Top-Up ----------
    topup_form = WalletTopUpForm(request.POST or None)
    if request.method == "POST" and request.POST.get("form_type") == "topup":
        if topup_form.is_valid():
            amount = topup_form.cleaned_data["amount"]
            donor.wallet_balance += amount
            donor.save(update_fields=["wallet_balance"])
            messages.success(request, f"Wallet topped up by R{amount:.2f}.")
            return redirect("donor_dashboard")

    # ---------- Fetch AI matches (from DB) ----------
    # Using Match model to display persisted matches (ranked by score)
    matches = (
        Match.objects.filter(donor=donor)
        .select_related("student")
        .order_by("-score")[:10]
    )

    # ---------- Transactions ----------
    transactions = Transaction.objects.filter(donor=donor).order_by("-created_at")[:20]

    context = {
        "donor": donor,
        "topup_form": topup_form,
        "matches": matches,
        "transactions": transactions,
        "csr_rank": donor.current_rank,
        "csr_progress": donor.progress_to_next,
        "csr_next_goal": donor.next_rank_goal,
    }
    return render(request, "predictor/donor_dashboard.html", context)
@login_required
@user_passes_test(is_donor)
def donor_wallet(request):
    # Get the donor for the logged-in user
    donor = get_object_or_404(Donor, user=request.user)

    if request.method == "POST":
        try:
            amount = Decimal(request.POST.get("amount", "0"))
        except (TypeError, ValueError):
            amount = Decimal("0")

        if amount > 0:
            donor.wallet_balance += amount
            donor.save(update_fields=["wallet_balance"])
            messages.success(request, f"Wallet topped up by R{amount:.2f}")
        else:
            messages.error(request, "Invalid top-up amount.")

        # Redirect to donor dashboard without donor_id
        return redirect("donor_dashboard")

    return render(request, "predictor/donor_wallet.html", {"donor": donor})

# -----------------------
# Donor requests access to view a student's academic records
# -----------------------
@login_required
@user_passes_test(is_donor)
def request_access_view(request, student_id):
    donor = request.user.donor
    student = get_object_or_404(Student, id=student_id)
    if request.method == "POST":
        message = request.POST.get("message", "")
        ar, created = AccessRequest.objects.get_or_create(donor=donor, student=student, defaults={"message": message})
        if created:
            messages.success(request, "Access request created — student will be notified.")
        else:
            messages.info(request, "An access request already exists for this student.")
        return redirect("donor_dashboard", donor_id=donor.id)
    # GET fallback: show a simple confirmation page
    return render(request, "predictor/request_access_confirm.html", {"student": student, "donor": donor})

# -----------------------
# Student view: approve / deny pending access requests
# -----------------------
@login_required
@user_passes_test(is_student)
def student_access_requests(request):
    student = request.user.student
    requests = AccessRequest.objects.filter(student=student, status="pending").order_by("created_at")
    if request.method == "POST":
        ar_id = request.POST.get("ar_id")
        action = request.POST.get("action")  # 'approve' or 'deny'
        ar = get_object_or_404(AccessRequest, id=ar_id, student=student)
        if action == "approve":
            ar.status = "approved"
            ar.reviewed_at = timezone.now()
            ar.save()
            messages.success(request, f"Approved access for {ar.donor.name}.")
        else:
            ar.status = "denied"
            ar.reviewed_at = timezone.now()
            ar.save()
            messages.info(request, f"Denied access for {ar.donor.name}.")
        return redirect("student_access_requests")
    return render(request, "predictor/student_access_requests.html", {"requests": requests, "student": student})

# -----------------------
# Donor viewing student records (only if approved)
@login_required
@user_passes_test(is_donor)
def view_student_records(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    donor = request.user.donor
    # Check if donor has a match with this student
    if not Match.objects.filter(student=student, donor=donor).exists() and not request.user.is_superuser:
        return HttpResponseForbidden("You cannot access this student's records.")
    
    records = AcademicRecord.objects.filter(student=student)
    return render(request, 'predictor/view_student_records.html', {'student': student, 'records': records})

# -----------------------
# Student uploads academic record (only student owner)
# -----------------------
@login_required
@user_passes_test(is_student)
def upload_academic(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.user.student.id != student.id and not request.user.is_superuser:
        return HttpResponseForbidden("You may only upload documents for your own student profile.")
    if request.method == "POST":
        form = AcademicUploadForm(request.POST, request.FILES)
        if form.is_valid():
            ar = form.save(commit=False)
            ar.student = student
            ar.save()
            messages.success(request, "Academic record uploaded.")
            return redirect("upload_academic", student_id=student.id)
    else:
        form = AcademicUploadForm()
    records = AcademicRecord.objects.filter(student=student).order_by("-uploaded_at")
    return render(request, "predictor/upload_academics.html", {"form": form, "student": student, "records": records})

# -----------------------
# Mock fund action (donor funds a match / bursary)
#@login_required
@user_passes_test(is_donor)
def fund_match(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    donor = request.user.donor

    # Security check: donor must own this match
    if match.donor.id != donor.id and not request.user.is_superuser:
        return HttpResponseForbidden("You can only fund matches belonging to your donor account.")

    if request.method != "POST":
        # Show confirmation page first
        return render(request, "predictor/fund_confirm.html", {"match": match, "donor": donor})

    # POST: Process funding
    try:
        amount = Decimal(request.POST.get("amount", "0"))
    except (TypeError, ValueError, ArithmeticError):
        messages.error(request, "Invalid amount.")
        return redirect("donor_dashboard", donor_id=donor.id)

    if amount <= 0:
        messages.error(request, "Amount must be greater than 0.")
        return redirect("donor_dashboard", donor_id=donor.id)

    if donor.wallet_balance < amount:
        messages.error(request, "Insufficient wallet balance.")
        return redirect("donor_wallet", donor_id=donor.id)

    # Deduct funds
    donor.wallet_balance -= amount
    donor.save()

    # Link to open bursary request if available
    bursary = BursaryRequest.objects.filter(student=match.student, fulfilled=False).first()

    tx = Transaction.objects.create(
    match=match,
    donor=donor,
    student=match.student,  
    bursary_request=bursary,
    amount=amount,
    tx_ref=f"MOCK-{timezone.now().strftime('%Y%m%d%H%M%S')}"
)


    # Mark match funded
    match.funded = True
    match.save()

    # Mark bursary fulfilled if needed
    if bursary:
        bursary.fulfilled = True
        bursary.save()

        # Special case: registration fee
        if bursary.priority == "registration_fee":
            rf = RegistrationFlag.objects.filter(student=bursary.student, flagged=True).first()
            if rf:
                rf.is_paid = True
                rf.flagged = False
                rf.flagged_reason = "Paid via donor micro-bursary"
                rf.save()
                bursary.student.registration_paid = True
                bursary.student.save()

    messages.success(request, f"Funded R{amount:.2f}. Transaction ref: {tx.tx_ref}")
    return redirect("donor_dashboard", donor_id=donor.id)


# -----------------------
# Queue alerts page for admins/university staff (list flagged registrations)
# -----------------------
@login_required
def queue_alerts(request):
    # allow only superuser or staff to view queue alerts (or extend with permission checks)
    if not request.user.is_superuser and not request.user.is_staff:
        return HttpResponseForbidden("Only staff can view queue alerts.")
    flags = RegistrationFlag.objects.filter(flagged=True).order_by("-created_at")
    return render(request, "predictor/queue_alerts.html", {"flags": flags})

@login_required
@user_passes_test(is_student)
def student_profile(request):
    student = get_object_or_404(Student, user=request.user)
    records = AcademicRecord.objects.filter(student=student).order_by("-uploaded_at")
    return render(request, "predictor/student_profile.html", {
        "student": student,
        "records": records,
    })



def custom_logout(request):
    if request.method == "POST":
        logout(request)
        return render(request, "registration/logged_out.html")
    else:
        # Redirect GET requests to home
        from django.shortcuts import redirect
        return redirect("home")

@login_required
def student_wallet(request):
    student = get_object_or_404(Student, user=request.user)

    context = {
        "student": student,
        "transactions": student.transactions.all().order_by("-created_at")[:20],
    }
    return render(request, "predictor/student_wallet.html", context)

@login_required
def donor_fund_student(request, student_id):
    donor = get_object_or_404(Donor, user=request.user)
    student = get_object_or_404(Student, id=student_id)

    if request.method == "POST":
        form = FundStudentForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data["amount"]
            if donor.wallet_balance >= amount:
                donor.wallet_balance -= amount
                student.wallet_balance += amount
                donor.save()
                student.save()

                Transaction.objects.create(
                    donor=donor, student=student, amount=amount,
                    description=f"Donor {donor.name} funded student {student.user.get_full_name()}"
                )
                messages.success(request, f"Successfully funded R {amount:.2f} to {student.user.get_full_name()}.")
                return redirect('donor_dashboard')
            else:
                messages.error(request, "Insufficient balance in donor wallet.")
    else:
        form = FundStudentForm()

    return render(request, "predictor/fund_student.html", {"form": form, "student": student})

@login_required
def transparency_dashboard(request):
    user = request.user
    # Wallet top-up form for donors
    topup_form = None
    if hasattr(user, 'donor'):
        donor = user.donor
        if request.method == "POST":
            topup_form = WalletTopUpForm(request.POST)
            if topup_form.is_valid():
                amount = topup_form.cleaned_data['amount']
                donor.wallet_balance += amount  # positive for top-up
                donor.save()
                messages.success(request, f"Wallet updated by R {amount:.2f}")
                return redirect('transparency_dashboard')
        else:
            topup_form = WalletTopUpForm()

    # Payments
    if hasattr(user, 'student'):
        payments = UniversityPayment.objects.filter(student=user.student).order_by('-timestamp')
    elif hasattr(user, 'donor'):
        payments = UniversityPayment.objects.filter(donor=user.donor).order_by('-timestamp')
    else:
        payments = UniversityPayment.objects.all().order_by('-timestamp')

    total_funded = sum([p.amount for p in payments if p.approved])

    # Aggregates for tables
    donors = payments.values('donor__user__first_name', 'donor__user__last_name')\
                     .annotate(total_funded=Sum('amount')).order_by('-total_funded')
    students = payments.values('student__user__first_name', 'student__user__last_name')\
                       .annotate(total_received=Sum('amount')).order_by('-total_received')

    # Daily funding for chart
    daily_funding = payments.values('timestamp__date')\
                            .annotate(total=Sum('amount'))\
                            .order_by('timestamp__date')

    context = {
        'payments': payments,
        'total_funded': total_funded,
        'donors': donors,
        'students': students,
        'daily_funding': daily_funding,
        'topup_form': topup_form,
    }

    return render(request, 'predictor/transparency_dashboard.html', context)