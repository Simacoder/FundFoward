from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from predictor import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    # Admin panel
    path("admin/", admin.site.urls),

    # Logout (must be before django.contrib.auth.urls so it takes precedence)
    path("accounts/logout/", LogoutView.as_view(template_name="registration/logged_out.html"), name="logout"),

    # Main app (home, student/donor registration, dashboard)
    path("", include("predictor.urls")),

    # Default auth URLs (login, password reset, etc.)
    path("accounts/", include("django.contrib.auth.urls")),

    # API endpoints
    path("api/", include("predictor.api_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
