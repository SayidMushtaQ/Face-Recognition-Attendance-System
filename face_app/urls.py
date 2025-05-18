from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('add-employee/', views.add_employee, name='add_employee'),
    path('attendance/', views.attendance_view, name='attendance'),
    path('attendance-list/', views.attendance_list, name='attendance_list'),
    path('video-feed/', views.video_feed, name='video_feed'),
]