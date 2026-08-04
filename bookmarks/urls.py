from django.urls import path
from . import views

app_name = 'bookmarks'

urlpatterns = [
    path('', views.bookmark_list, name='list'),
    path('toggle/<int:content_type_id>/<int:object_id>/', views.toggle_bookmark_view, name='toggle'),
]
