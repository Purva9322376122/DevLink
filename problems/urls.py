from django.urls import path
from . import views

urlpatterns = [
    path('', views.problem_list, name='problem_list'),
    path('create/', views.create_problem, name='create_problem'),
    path('<int:problem_id>/', views.problem_detail, name='problem_detail'),
    path('<int:problem_id>/edit/', views.edit_problem, name='edit_problem'),
    path('<int:problem_id>/delete/', views.delete_problem, name='delete_problem'),
    path('<int:problem_id>/history/', views.problem_history, name='problem_history'),
    path('<int:problem_id>/history/<int:revision_id>/restore/',
         views.restore_problem_revision, name='restore_problem_revision'),
    path('report/', views.report_content, name='report_content'),
    path('tags/', views.tag_list, name='tag_list'),
    path('tags/autocomplete/', views.tag_autocomplete, name='tag_autocomplete'),
    path('tags/<slug:tag_slug>/', views.tag_detail, name='tag_detail'),
    path('reports/queue/', views.report_queue, name='report_queue'),
    path('reports/<int:report_id>/resolve/', views.resolve_report, name='resolve_report'),
]
