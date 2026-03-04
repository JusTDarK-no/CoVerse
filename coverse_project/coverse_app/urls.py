# coverse_app/urls.py
from django.urls import path
from . import views

app_name = 'coverse_app'

urlpatterns = [
    # Проекты
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

    # ===== ИЗМЕНЕНО: post_comments → post_detail =====
    path('post/<int:post_pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('post/<int:post_pk>/comment/create/', views.CommentCreateView.as_view(), name='comment_create'),
    path('post/<int:post_pk>/comment/<int:comment_pk>/reply/', views.ReplyCreateView.as_view(), name='comment_reply'),

    # ===== НОВОЕ: История изменений поста =====
    path('post/<int:post_pk>/history/', views.PostHistoryView.as_view(), name='post_history'),

    # Предложения
    path('post/<int:post_pk>/suggestion/create/',
         views.SuggestionCreateView.as_view(),
         name='suggestion_create'),
    path('post/<int:post_pk>/suggestions/',
         views.PostSuggestionsListView.as_view(),
         name='post_suggestions_list'),
    path('project/<int:project_pk>/suggestions/',
         views.ProjectSuggestionsView.as_view(),
         name='project_suggestions'),
    path('suggestion/<int:suggestion_pk>/',
         views.SuggestionDetailView.as_view(),
         name='suggestion_detail'),
    path('suggestion/<int:suggestion_pk>/response/',
         views.SuggestionResponseView.as_view(),
         name='suggestion_response'),
    path('suggestion/<int:suggestion_pk>/post/<int:post_pk>/edit/',
         views.SuggestionAcceptEditView.as_view(),
         name='suggestion_accept_edit'),
    path('suggestion/attachment/<int:attachment_pk>/download/',
         views.download_suggestion_attachment,
         name='download_suggestion_attachment'),
]