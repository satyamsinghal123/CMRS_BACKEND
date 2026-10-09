from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.views import CMRSObtainPairView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/token/", CMRSObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/", include("core.urls")),
    path("api/", include("customers.urls")),
    path("api/", include("loans.urls")),
    path("api/", include("cashcollections.urls")),
    path("api/", include("reconciliation.urls")),
    path("api/", include("deposits.urls")),
    path("api/", include("dashboard.urls")),
]
