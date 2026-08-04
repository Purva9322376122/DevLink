from django.urls import path
from . import views

app_name = 'reputation'

urlpatterns = [
    path('', views.reputation_view, name='reputation'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
]
