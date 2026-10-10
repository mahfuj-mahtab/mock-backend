from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/profile/", include("apps.profiles.urls")),
    path("api/v1/mock-prep/", include("apps.mock_prep.urls")),
    path("api/v1/admin/mock-prep/", include("apps.mock_prep.admin_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
