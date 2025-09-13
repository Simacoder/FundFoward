# predictor/forms.py
from django import forms
from django import forms
from django.contrib.auth.models import User
from .models import Student, Donor, BursaryRequest, AcademicRecord


class StudentRegistrationForm(forms.ModelForm):
    """Used for registering new students along with login credentials."""
    
    email = forms.EmailField(required=True, label="Email")
    password1 = forms.CharField(
        label="Password", 
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label="Confirm Password", 
        widget=forms.PasswordInput
    )

    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'student_number',
            'course', 'gpa', 'need_score', 'province'
        ]

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Passwords do not match.")
        return cleaned_data


class DonorRegistrationForm(forms.ModelForm):
    """Used for registering new donors."""
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    class Meta:
        model = Donor
        fields = [
            'name', 'donor_type', 'preferred_course',
            'min_gpa', 'max_amount', 'wallet_balance'
        ]


class BursaryRequestForm(forms.ModelForm):
    """Used for students requesting bursaries."""
    class Meta:
        model = BursaryRequest
        fields = ['requested_amount', 'reason', 'priority']


class AcademicUploadForm(forms.ModelForm):
    """Used for uploading academic documents."""
    class Meta:
        model = AcademicRecord
        fields = ['title', 'file']


class WalletTopUpForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Use positive to add, negative to subtract"
    )
class TopUpForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=1)

class FundStudentForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=1)