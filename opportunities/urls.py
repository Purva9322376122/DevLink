from django.urls import path
from . import views

urlpatterns = [
    path('', views.opportunity_list, name='opportunity_list'),
    path('create/', views.create_opportunity, name='create_opportunity'),
    path('<int:id>/', views.opportunity_detail, name='opportunity_detail'),
    path('invite/', views.send_invitation, name='send_invitation'),
    path('connections/', views.connection_list, name='connection_list'),
    path('connection/<int:pk>/remove/', views.remove_connection, name='remove_connection'),
    path('invitations/', views.invitation_list, name='invitation_list'),
    path('invitations/sent/', views.sent_invitations, name='sent_invitations'),
    path('invitation/<int:pk>/accept/', views.accept_invitation, name='accept_invitation'),
    path('invitation/<int:pk>/reject/', views.reject_invitation, name='reject_invitation'),
    path('<int:pk>/apply/', views.apply_opportunity, name='apply_opportunity'),
    path('<int:pk>/applications/', views.view_applications, name='view_applications'),
    # Opportunity owner — manages received applications
    path('applications/manage/', views.application_list, name='application_list'),
    # Applicant — views their own submitted applications
    path('applications/mine/', views.applications, name='my_applications'),
    path('application/<int:app_id>/accept/', views.accept_application, name='accept_application'),
    path('application/<int:app_id>/reject/', views.reject_application, name='reject_application'),
    path('chat/<str:username>/', views.chat, name='chat'),
    path('messages/', views.messages_list, name='messages_list'),
]
