# coverse_app/admin_urls.py
from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('projects/', views.admin_projects, name='admin_projects'),
    path('users/', views.admin_users, name='admin_users'),
    path('moderation-log/', views.admin_moderation_log, name='admin_moderation_log'),

    # Модерация проектов
    path('project/<int:project_id>/hide/', views.hide_project_with_reason, name='hide_project_with_reason'),
    path('project/<int:project_id>/unhide/', views.unhide_project, name='unhide_project'),

    # Модерация постов
    path('post/<int:post_id>/hide/', views.hide_post_with_reason, name='hide_post_with_reason'),

    # Блокировка пользователей
    path('user/<int:user_id>/block/', views.block_user_with_reason, name='block_user_with_reason'),
    path('user/<int:user_id>/unblock/', views.unblock_user, name='unblock_user'),

    # Управление тегами
    path('tags/', views.admin_tags, name='admin_tags'),
    path('tag/create/', views.TagCreateView.as_view(), name='tag_create'),
    path('tag/<int:pk>/update/', views.TagUpdateView.as_view(), name='tag_update'),
    path('tag/<int:pk>/delete/', views.TagDeleteView.as_view(), name='tag_delete'),

    # Модерация комментариев
    path('comment/<int:comment_id>/hide/', views.hide_comment_with_reason, name='hide_comment_with_reason'),

]