from django.urls import path
from . import views

app_name = 'messages'

urlpatterns = [
    path('', views.message_list, name='list'),
    path('start/<str:username>/', views.start_conversation, name='start'),
    path('<int:conversation_id>/', views.chat_room, name='room'),
]
