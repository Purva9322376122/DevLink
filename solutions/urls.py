from django.urls import path
from . import views

urlpatterns = [
    path('create/<int:problem_id>/', views.create_solution, name='solution_create'),
    path('problem/<int:problem_id>/', views.solution_list, name='solution_list'),
    path('vote/<int:solution_id>/', views.toggle_vote, name='toggle_vote'),
    path('accept/<int:solution_id>/', views.accept_solution, name='accept_solution'),
    path('comment/<int:solution_id>/', views.add_comment, name='add_comment'),
    path('<int:solution_id>/edit/', views.edit_solution, name='edit_solution'),
    path('<int:solution_id>/delete/', views.delete_solution, name='delete_solution'),
    path('<int:solution_id>/history/', views.solution_history, name='solution_history'),
    path('comment/<int:comment_id>/edit/', views.edit_comment_view, name='edit_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment_view, name='delete_comment'),
    path('preview/', views.preview_markdown, name='preview_markdown'),
]
