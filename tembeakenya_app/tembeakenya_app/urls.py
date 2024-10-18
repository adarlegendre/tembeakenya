from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("tembeakenyasite/", include("tembeakenyasite.urls")),
    path("admin/", admin.site.urls),
]