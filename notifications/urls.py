from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('dropdown/', views.notification_dropdown, name='dropdown'),
    path('unread-count/', views.unread_count_view, name='unread_count'),
    path('<int:pk>/read/', views.mark_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_read_view, name='mark_all_read'),
]
