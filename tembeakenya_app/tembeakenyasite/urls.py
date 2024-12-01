from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("areamaps", views.attraction_detail, name="attraction_detail"),
    path("map", views.attraction_map, name="attraction_map"),

]