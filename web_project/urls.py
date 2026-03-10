from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("flat.urls")),
    path("login/", auth_views.LoginView.as_view(), name="login"),
]

urlpatterns += staticfiles_urlpatterns()