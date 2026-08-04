from django.urls import path
from . import views

app_name = 'collections'

urlpatterns = [
    path('', views.collection_list, name='list'),
    path('create/', views.create_collection_view, name='create'),
    path('<int:pk>/', views.collection_detail, name='detail'),
    path('<int:pk>/edit/', views.edit_collection_view, name='edit'),
    path('<int:pk>/delete/', views.delete_collection_view, name='delete'),
    path('add-item/', views.add_item_view, name='add_item'),
    path('remove-item/<int:item_id>/', views.remove_item_view, name='remove_item'),
]
