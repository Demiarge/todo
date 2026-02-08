from django.urls import path
from django.shortcuts import redirect
from . import views
from .api_views import TaskListCreateAPI, TaskDetailAPI, notification_unread_count, notification_latest

app_name = 'tasks'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('task/', lambda r: redirect('tasks:dashboard')),
    path('task/create/', views.task_create, name='task_create'),
    path('task/<slug:slug>/', views.task_detail, name='task_detail'),
    path('task/<slug:slug>/edit/', views.task_edit, name='task_edit'),
    path('task/<slug:slug>/delete/', views.task_delete, name='task_delete'),
    path('task/<slug:slug>/status/', views.task_update_status, name='task_update_status'),
    path('task/<slug:slug>/comment/', views.task_add_comment, name='task_add_comment'),
    path('notifications/', views.notification_list, name='notifications'),
    path('notifications/<int:pk>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('profile/', views.profile_view, name='profile'),
    path('api/users/search/', views.user_search_api, name='user_search_api'),
    path('api/tasks/', TaskListCreateAPI.as_view(), name='api_task_list_create'),
    path('api/tasks/<int:pk>/', TaskDetailAPI.as_view(), name='api_task_detail'),
    path('api/notifications/unread-count/', notification_unread_count, name='api_notification_unread_count'),
    path('api/notifications/latest/', notification_latest, name='api_notification_latest'),
]
