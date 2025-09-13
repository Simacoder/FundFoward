from django.db import models
from decimal import Decimal
from django.contrib.auth.models import User
from django.utils import timezone

class Donor(models.Model):
    DONOR_TYPES = (('alumni', 'Alumni'), ('corporate', 'Corporate'), ('ngo', 'NGO'))

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=150)
    donor_type = models.CharField(max_length=30, choices=DONOR_TYPES)
    preferred_course = models.CharField(max_length=120, blank=True, null=True)
    min_gpa = models.FloatField(default=0.0)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('5000.00'))

    # Wallet / financials
    wallet_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_donated = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    # Gamification / CSR
    csr_score = models.IntegerField(default=0)  # points (e.g. 1 point per R100 donated)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.donor_type})"

    # ---------- CSR helpers ----------
    def update_csr_score(self, amount):
        """
        Update donor totals and CSR score when they donate `amount`.
        - amount: Decimal or float or int (Rands)
        - Points rule: 1 point per R100 donated (adjust if needed)
        """
        if amount is None:
            return

        # Normalize to Decimal
        amount = Decimal(str(amount)).quantize(Decimal('0.01'))

        # compute points (integer)
        points = int(amount // Decimal('100.00'))

        # Update totals and score
        # Use Python-side update (simple). If you expect concurrent updates use F() expressions.
        self.total_donated = (self.total_donated or Decimal('0.00')) + amount
        self.csr_score = (self.csr_score or 0) + points
        self.save(update_fields=['total_donated', 'csr_score'])

    @property
    def current_rank(self):
        """Return human rank label based on csr_score."""
        s = self.csr_score or 0
        if s >= 1000:
            return "Gold"
        if s >= 500:
            return "Silver"
        if s >= 100:
            return "Bronze"
        return "Newbie"

    @property
    def next_rank_goal(self):
        """Return the CSR score needed for the next rank, or None if already max."""
        s = self.csr_score or 0
        if s >= 1000:
            return None
        if s >= 500:
            return 1000
        if s >= 100:
            return 500
        return 100

    @property
    def progress_to_next(self):
        """Return integer percent progress to next rank (0-100). If no next rank -> 100."""
        goal = self.next_rank_goal
        if not goal:
            return 100
        s = self.csr_score or 0
        pct = int((s / goal) * 100)
        return max(0, min(pct, 100))

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)  # <-- added
    student_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gpa = models.FloatField(default=0.0)
    course = models.CharField(max_length=120, blank=True, null=True)
    need_score = models.FloatField(default=5.0)  # scale 0-10
    province = models.CharField(max_length=100, blank=True, null=True)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    registration_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student_number} - {self.first_name} {self.last_name}"

class AcademicRecord(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='academic_records/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.student_number} - {self.title}"

class BursaryRequest(models.Model):
    PRIORITY_CHOICES = (('registration_fee','Registration Fee'), ('tuition','Tuition'), ('living','Living Costs'))
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    requested_amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField(blank=True)
    priority = models.CharField(max_length=30, choices=PRIORITY_CHOICES, default='registration_fee')
    fulfilled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"BR-{self.id} ({self.student.student_number}) - {self.priority} - {'Fulfilled' if self.fulfilled else 'Open'}"

class Match(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    donor = models.ForeignKey('Donor', on_delete=models.CASCADE)
    score = models.FloatField()
    top_features = models.JSONField(null=True, blank=True)  # <-- add this
    matched_at = models.DateTimeField(auto_now_add=True)
    funded = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'donor')



class Transaction(models.Model):
    match = models.ForeignKey(Match, on_delete=models.SET_NULL, null=True, blank=True)
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name="transactions")
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    bursary_request = models.ForeignKey(BursaryRequest, on_delete=models.SET_NULL, null=True, blank=True)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tx_ref = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tx {self.id} | Donor: {self.donor.name} | Amount: {self.amount}"

class RegistrationFlag(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    semester = models.CharField(max_length=20)
    is_paid = models.BooleanField(default=False)
    flagged = models.BooleanField(default=False)
    flagged_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class AccessRequest(models.Model):
    STATUS_CHOICES = (('pending', 'Pending'), ('approved', 'Approved'), ('denied', 'Denied'))
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('donor', 'student')  # one request per donor-student pair

    def __str__(self):
        return f"AccessRequest({self.donor} -> {self.student}) [{self.status}]"


class UniversityPayment(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name="university_payments")
    donor = models.ForeignKey('Donor', null=True, blank=True, on_delete=models.SET_NULL)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(
        max_length=50,
        choices=[('bursary','Bursary'),('tuition','Tuition'),('living','Living Costs')],
        default='bursary'
    )
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    approved = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.student} - R{self.amount} from {self.donor or 'University/Trust'}"