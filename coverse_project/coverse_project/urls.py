# coverse_project/urls.py
from django.contrib import admin
from django.urls import path, include
from coverse_app.views import RegisterView
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('coverse_app.urls')),  # основные маршруты

    path('accounts/register/', RegisterView.as_view(), name='register'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin-panel/', include('coverse_app.admin_urls')),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)