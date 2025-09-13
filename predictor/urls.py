# predictor/urls.py
from django.urls import path
from predictor import views
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views
from .views import DonorLoginView
from . import views


urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Services
    path('services/', views.services, name='services'),
    path('about/', views.about_view, name='about'),

    path('transparency/', views.transparency_dashboard, name='transparency_dashboard'),



    # Registration
    path('student/register/', views.student_register, name='student_register'),
    path('donor/register/', views.donor_register, name='donor_register'),

    path('donor/login/', DonorLoginView.as_view(), name='donor_login'),

    # Student actions
    path('student/<int:student_id>/request_fee/', views.request_fee, name='request_fee'),
    path('student/<int:student_id>/upload-academic/', views.upload_academic, name='upload_academic'),
    path("student/profile/", views.student_profile, name="student_profile"),
    #path("accounts/logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path(
    "accounts/logout/",
    LogoutView.as_view(template_name="registration/logged_out.html"),
    name="logout"
),
    # predictor/urls.py
    path("donor/logout/", views.donor_logout, name="donor_logout"),

    


    # Donor actions
    # Donor dashboard
    # Remove donor_id from path
    path('donor/dashboard/', views.donor_dashboard, name='donor_dashboard'),
    path('donor/wallet/', views.donor_wallet, name='donor_wallet'),
    path('donor/fund/<int:match_id>/', views.fund_match, name='fund_match'),

    # funds
    path("student/wallet/", views.student_wallet, name="student_wallet"),
    path("donor/fund/<int:student_id>/", views.donor_fund_student, name="fund_student"),
    # Queue alerts
    path('admin/queue-alerts/', views.queue_alerts, name='queue_alerts'),
]
