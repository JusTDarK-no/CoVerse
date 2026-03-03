# coverse_app/urls.py
from django.urls import path
from . import views

app_name = 'coverse_app'  # для обратных URL: {% url 'coverse_app:project_list' %}


urlpatterns = [
    path('', views.ProjectListView.as_view(), name='project_list'),
    path('project/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('project/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('project/<int:project_pk>/section/create/', views.SectionCreateView.as_view(), name='section_create'),
    path('section/<int:pk>/', views.SectionDetailView.as_view(), name='section_detail'),
    path('section/<int:section_pk>/post/create/', views.PostCreateView.as_view(), name='post_create'),
    path('project/<int:pk>/update/', views.ProjectUpdateView.as_view(), name='project_update'),
    path('project/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
    path('my-projects/', views.MyProjectsView.as_view(), name='my_projects'),
    path('post/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post_delete'),

    # Комментарии
    path('post/<int:post_pk>/comments/', views.PostCommentsView.as_view(), name='post_comments'),
    path('post/<int:post_pk>/comment/create/', views.CommentCreateView.as_view(), name='comment_create'),
    path('post/<int:post_pk>/comment/<int:comment_pk>/reply/', views.ReplyCreateView.as_view(), name='comment_reply'),
]
