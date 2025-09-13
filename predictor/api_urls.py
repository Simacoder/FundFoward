# predictor/api_urls.py
from django.urls import path
from . import api_views

urlpatterns = [
    path('match-score/', api_views.match_score, name='api_match_score'),
    path('fund/', api_views.fund_student, name='api_fund_student'),
    path('registration-alerts/', api_views.registration_alerts, name='api_registration_alerts'),
]
