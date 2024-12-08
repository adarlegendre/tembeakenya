from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("areamaps", views.attraction_detail, name="attraction_detail"),
    path("map", views.attraction_map, name="attraction_map"),
    path('insert-image/', views.insert_image_view, name='insert_image'),
    
    path('delete-image/<int:image_id>/', views.delete_image_view, name='delete_image'),
    path('manage-images/<int:attraction_id>/', views.manage_images_view, name='manage_images'),
]