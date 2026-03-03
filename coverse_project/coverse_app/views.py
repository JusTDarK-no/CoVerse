# coverse_app/views.py
from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from .models import *
from django.views.generic import DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django import forms
from django.db import models  # для Q
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.views.generic import View
from .forms import PostForm
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.contrib.auth.models import User
from .models import Project, Suggestion
from django.contrib import messages
from .forms import *


# coverse_app/views.py

from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование проекта (только автором)"""
    model = Project
    fields = ['title', 'description', 'cover_image', 'privacy', 'status', 'tags']
    template_name = 'coverse_app/project_form.html'  # используем тот же шаблон, что и для создания
    success_url = reverse_lazy('coverse_app:my_projects')

    def test_func(self):
        # Только автор может редактировать
        project = self.get_object()
        return project.author == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактировать «{self.object.title}»'
        return context


# coverse_app/views.py

class ProjectListView(ListView):
    model = Project
    template_name = 'coverse_app/project_list.html'
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        queryset = Project.objects.select_related('author', 'author__profile')

        if self.request.user.is_authenticated:
            public_active = Q(privacy='public', moderation_status='active')
            own_hidden = Q(author=self.request.user, moderation_status='hidden_by_moderation')
            queryset = queryset.filter(public_active | own_hidden)
        else:
            queryset = queryset.filter(privacy='public', moderation_status='active')

        # Поиск и фильтр по статусу (если у вас есть)
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )

        status_filter = self.request.GET.get('status')
        if status_filter and status_filter in dict(Project.STATUS_CHOICES):
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Проекты на CoVerse'
        context['search_query'] = self.request.GET.get('q', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['status_choices'] = Project.STATUS_CHOICES  # передаём варианты в шаблон
        return context

class ProjectCreateView(LoginRequiredMixin, CreateView):
    """Создание нового проекта (только для авторизованных)"""
    model = Project
    fields = ['title', 'description', 'cover_image', 'privacy', 'status', 'tags']
    template_name = 'coverse_app/project_form.html'
    success_url = reverse_lazy('coverse_app:project_list')

    def form_valid(self, form):
        # Автоматически назначаем автора
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создать проект'
        return context




class ProjectDetailView(DetailView):
    """Детали проекта"""
    model = Project
    template_name = 'coverse_app/project_detail.html'
    context_object_name = 'project'

    def get_queryset(self):
        queryset = Project.objects.select_related('author', 'author__profile')

        if self.request.user.is_authenticated:
            public_active = Q(privacy='public', moderation_status='active')
            own_hidden = Q(author=self.request.user, moderation_status='hidden_by_moderation')
            queryset = queryset.filter(public_active | own_hidden)
        else:
            queryset = queryset.filter(privacy='public', moderation_status='active')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        context['title'] = project.title
        # Загружаем разделы с постами (оптимизация запросов)
        context['sections'] = project.sections.prefetch_related('posts').all()
        return context

from django.views.generic.edit import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')  # после регистрации — на вход

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Регистрация'
        return context

class MyProjectsView(LoginRequiredMixin, ListView):
    """Список проектов текущего пользователя"""
    model = Project
    template_name = 'coverse_app/my_projects.html'
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        # Только проекты текущего пользователя
        return Project.objects.filter(author=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Мои проекты'
        return context

class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление проекта (только автором)"""
    model = Project
    template_name = 'coverse_app/project_confirm_delete.html'
    success_url = reverse_lazy('coverse_app:my_projects')

    def test_func(self):
        # Проверка: только автор может удалить
        project = self.get_object()
        return project.author == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Удалить проект «{self.object.title}»?'
        return context


# coverse_app/views.py

class PostCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'coverse_app/post_form.html'

    def test_func(self):
        section = get_object_or_404(Section, pk=self.kwargs['section_pk'])
        return section.project.author == self.request.user

    def form_valid(self, form):
        form.instance.section = get_object_or_404(Section, pk=self.kwargs['section_pk'])
        response = super().form_valid(form)

        # Обработка множественных изображений
        images = self.request.FILES.getlist('images')  # ← КЛЮЧЕВОЙ МОМЕНТ
        if len(images) > 5:
            # Добавляем ошибку в форму и возвращаем её
            form.add_error(None, "Можно загрузить не более 5 изображений.")
            return self.form_invalid(form)

        # Валидация формата
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        for img in images:
            ext = os.path.splitext(img.name)[1].lower()
            if ext not in valid_extensions:
                form.add_error(None, "Разрешены только изображения: JPG, PNG, GIF.")
                return self.form_invalid(form)

        # Сохраняем изображения
        for img in images:
            PostImage.objects.create(post=self.object, image=img)

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = get_object_or_404(Section, pk=self.kwargs['section_pk'])
        return context

    def get_success_url(self):
        return reverse('coverse_app:section_detail', kwargs={'pk': self.object.section.pk})


# ===== СОЗДАНИЕ РАЗДЕЛА =====
class SectionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Section
    fields = ['title', 'section_type', 'description', 'order']
    template_name = 'coverse_app/section_form.html'

    def test_func(self):
        # Только автор проекта может создавать разделы
        project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        return project.author == self.request.user

    def form_valid(self, form):
        form.instance.project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('coverse_app:project_detail', kwargs={'pk': self.kwargs['project_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        return context



# ===== СОЗДАНИЕ ПОСТА =====

class SectionDetailView(DetailView):
    """Страница отдельного раздела с постами"""
    model = Section
    template_name = 'coverse_app/section_detail.html'
    context_object_name = 'section'


    def get_queryset(self):
        # Доступ: только если проект публичный или пользователь — автор
        user = self.request.user
        qs = Section.objects.select_related('project__author')
        if user.is_authenticated:
            return qs.filter(
                Q(project__privacy='public') | Q(project__author=user)
            )
        else:
            return qs.filter(project__privacy='public')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        section = self.object
        project = section.project


        # Сортировка: НОВЫЕ ПОСТЫ СВЕРХУ
        posts = section.posts.all().order_by('-created_at')

        context['posts'] = posts
        context['project'] = project
        context['can_edit'] = (self.request.user == project.author)
        context['title'] = f"{section.get_section_type_display()}: {section.title}"
        return context

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Скрытие поста (soft delete)"""

    def test_func(self):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        return post.section.project.author == self.request.user

    def post(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        post.is_deleted = True
        post.deleted_at = timezone.now()
        post.save(update_fields=['is_deleted', 'deleted_at'])
        return HttpResponseRedirect(
            reverse('coverse_app:section_detail', kwargs={'pk': post.section.pk})
        )


def superuser_required(view_func):
    """Декоратор: только суперпользователи"""
    return user_passes_test(lambda u: u.is_superuser)(view_func)

@superuser_required
def admin_dashboard(request):
    """Главная страница админ-панели"""
    stats = {
        'total_users': User.objects.count(),
        'total_projects': Project.objects.count(),
        'public_projects': Project.objects.filter(privacy='public').count(),
        'total_suggestions': Suggestion.objects.count(),
        'new_suggestions': Suggestion.objects.filter(status='new').count(),
    }
    return render(request, 'admin_panel/dashboard.html', {'stats': stats})

@superuser_required
def admin_projects(request):
    """Управление проектами"""
    projects = Project.objects.select_related('author').order_by('-created_at')
    return render(request, 'admin_panel/projects.html', {'projects': projects})

@superuser_required
def admin_users(request):
    """Управление пользователями"""
    users = User.objects.order_by('-date_joined')
    return render(request, 'admin_panel/users.html', {'users': users})

@superuser_required
def admin_suggestions(request):
    """Модерация предложений"""
    suggestions = Suggestion.objects.select_related(
        'post__section__project', 'author'
    ).order_by('-created_at')
    return render(request, 'admin_panel/suggestions.html', {'suggestions': suggestions})

@superuser_required
def block_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.is_blocked = True
    profile.blocked_at = timezone.now()
    profile.save()
    messages.success(request, f"Пользователь {user.username} заблокирован.")
    return HttpResponseRedirect(reverse('admin_users'))

@superuser_required
def unblock_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.is_blocked = False
    profile.blocked_at = None
    profile.save()
    messages.success(request, f"Пользователь {user.username} разблокирован.")
    return HttpResponseRedirect(reverse('admin_users'))

@superuser_required
def hide_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    project.moderation_status = 'hidden_by_moderation'
    project.moderation_hidden_at = timezone.now()
    project.save()
    messages.success(request, f"Проект «{project.title}» скрыт.")
    return HttpResponseRedirect(reverse('admin_projects'))

@superuser_required
def delete_post_moderation(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.moderation_deleted = True
    post.moderation_deleted_at = timezone.now()
    post.save()
    messages.success(request, "Пост скрыт модерацией.")
    return HttpResponseRedirect(reverse('admin_suggestions'))

@superuser_required
def block_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.is_blocked = True
    profile.blocked_at = timezone.now()
    profile.save()
    messages.success(request, f"Пользователь {user.username} заблокирован.")
    return HttpResponseRedirect(reverse('admin_panel:admin_users'))  # ← ИСПРАВЛЕНО

@superuser_required
def unblock_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.is_blocked = False
    profile.blocked_at = None
    profile.save()
    messages.success(request, f"Пользователь {user.username} разблокирован.")
    return HttpResponseRedirect(reverse('admin_panel:admin_users'))  # ← ИСПРАВЛЕНО

@superuser_required
def hide_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    project.moderation_status = 'hidden_by_moderation'
    project.moderation_hidden_at = timezone.now()
    project.save()
    messages.success(request, f"Проект «{project.title}» скрыт.")
    return HttpResponseRedirect(reverse('admin_panel:admin_projects'))  # ← ИСПРАВЛЕНО

@superuser_required
def delete_post_moderation(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.moderation_deleted = True
    post.moderation_deleted_at = timezone.now()
    post.save()
    messages.success(request, "Пост скрыт модерацией.")
    return HttpResponseRedirect(reverse('admin_panel:admin_suggestions'))  # ← ИСПРАВЛЕНО

# ===== УПРАВЛЕНИЕ ТЕГАМИ =====

class TagCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Tag
    fields = ['name']
    template_name = 'admin_panel/tag_form.html'
    success_url = reverse_lazy('admin_panel:admin_tags')

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создать тег'
        return context


class TagUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Tag
    fields = ['name']
    template_name = 'admin_panel/tag_form.html'
    success_url = reverse_lazy('admin_panel:admin_tags')

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактировать тег «{self.object.name}»'
        return context


class TagDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Tag
    template_name = 'admin_panel/tag_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:admin_tags')

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Удалить тег «{self.object.name}»?'
        return context


@superuser_required
def admin_tags(request):
    """Список всех тегов"""
    tags = Tag.objects.all().order_by('name')
    return render(request, 'admin_panel/tags.html', {'tags': tags})


@superuser_required
def unhide_project(request, project_id):
    """Восстановить скрытый проект"""
    project = get_object_or_404(Project, id=project_id)
    project.moderation_status = 'active'
    project.moderation_hidden_at = None
    project.save()
    messages.success(request, f"Проект «{project.title}» восстановлен.")
    return HttpResponseRedirect(reverse('admin_panel:admin_projects'))


# ===== МОДЕРАЦИЯ ПРОЕКТОВ =====

@superuser_required
def hide_project_with_reason(request, project_id):
    """Скрытие проекта с указанием причины"""
    project = get_object_or_404(Project, id=project_id)

    if request.method == 'POST':
        form = ModerationReasonForm(request.POST)
        if form.is_valid():
            # Скрываем проект
            project.moderation_status = 'hidden_by_moderation'
            project.moderation_hidden_at = timezone.now()
            project.save()

            # Логируем действие
            ModerationLog.objects.create(
                moderator=request.user,
                action='hide_project',
                project=project,
                reason=form.cleaned_data['reason']
            )

            messages.success(request, f"Проект «{project.title}» скрыт.")
            return HttpResponseRedirect(reverse('admin_panel:admin_projects'))
    else:
        form = ModerationReasonForm()

    return render(request, 'admin_panel/moderation_form.html', {
        'form': form,
        'title': f'Скрыть проект «{project.title}»',
        'action_url': reverse('admin_panel:hide_project_with_reason', kwargs={'project_id': project_id}),
        'cancel_url': reverse('admin_panel:admin_projects'),
    })


@superuser_required
def unhide_project(request, project_id):
    """Восстановить скрытый проект (причина не обязательна)"""
    project = get_object_or_404(Project, id=project_id)
    project.moderation_status = 'active'
    project.moderation_hidden_at = None
    project.save()

    # Логируем действие
    ModerationLog.objects.create(
        moderator=request.user,
        action='unhide_project',
        project=project,
        reason='Восстановлен модератором'
    )

    messages.success(request, f"Проект «{project.title}» восстановлен.")
    return HttpResponseRedirect(reverse('admin_panel:admin_projects'))


# ===== МОДЕРАЦИЯ ПОСТОВ =====

@superuser_required
def hide_post_with_reason(request, post_id):
    """Скрытие поста с указанием причины"""
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        form = ModerationReasonForm(request.POST)
        if form.is_valid():
            # Скрываем пост
            post.moderation_deleted = True
            post.moderation_deleted_at = timezone.now()
            post.save()

            # Логируем действие
            ModerationLog.objects.create(
                moderator=request.user,
                action='hide_post',
                post=post,
                reason=form.cleaned_data['reason']
            )

            messages.success(request, "Пост скрыт модерацией.")
            return HttpResponseRedirect(
                reverse('coverse_app:section_detail', kwargs={'pk': post.section.pk})
            )
    else:
        form = ModerationReasonForm()

    return render(request, 'admin_panel/moderation_form.html', {
        'form': form,
        'title': f'Скрыть пост «{post.title or "Без названия"}»',
        'action_url': reverse('admin_panel:hide_post_with_reason', kwargs={'post_id': post_id}),
        'cancel_url': reverse('coverse_app:section_detail', kwargs={'pk': post.section.pk}),
    })


# ===== БЛОКИРОВКА ПОЛЬЗОВАТЕЛЕЙ =====

@superuser_required
def block_user_with_reason(request, user_id):
    """Блокировка пользователя с указанием причины"""
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = UserBlockReasonForm(request.POST)
        if form.is_valid():
            # Блокируем пользователя
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.is_blocked = True
            profile.blocked_at = timezone.now()
            profile.save()

            # Логируем действие
            ModerationLog.objects.create(
                moderator=request.user,
                action='block_user',
                user=user,
                reason=form.cleaned_data['reason']
            )

            messages.success(request, f"Пользователь {user.username} заблокирован.")
            return HttpResponseRedirect(reverse('admin_panel:admin_users'))
    else:
        form = UserBlockReasonForm()

    return render(request, 'admin_panel/moderation_form.html', {
        'form': form,
        'title': f'Заблокировать пользователя «{user.username}»',
        'action_url': reverse('admin_panel:block_user_with_reason', kwargs={'user_id': user_id}),
        'cancel_url': reverse('admin_panel:admin_users'),
    })


@superuser_required
def unblock_user(request, user_id):
    """Разблокировка пользователя"""
    user = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.is_blocked = False
    profile.blocked_at = None
    profile.save()

    # Логируем действие
    ModerationLog.objects.create(
        moderator=request.user,
        action='unblock_user',
        user=user,
        reason='Разблокирован модератором'
    )

    messages.success(request, f"Пользователь {user.username} разблокирован.")
    return HttpResponseRedirect(reverse('admin_panel:admin_users'))


# ===== ЛОГ МОДЕРАЦИИ =====

@superuser_required
def admin_moderation_log(request):
    """Просмотр лога модерации"""
    logs = ModerationLog.objects.select_related(
        'moderator', 'project', 'post', 'user'
    ).order_by('-created_at')

    return render(request, 'admin_panel/moderation_log.html', {'logs': logs})


# ===== КОММЕНТАРИИ =====

class CommentCreateView(LoginRequiredMixin, CreateView):
    """Создание комментария к посту"""
    model = Comment
    form_class = CommentForm
    template_name = 'coverse_app/post_comments.html'

    def form_valid(self, form):
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_pk'])
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('coverse_app:post_comments', kwargs={'post_pk': self.kwargs['post_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = get_object_or_404(Post, pk=self.kwargs['post_pk'])
        context['post'] = post
        context['project'] = post.section.project
        context['section'] = post.section
        context['comments'] = post.comments.filter(parent__isnull=True).select_related(
            'author', 'author__profile'
        ).prefetch_related(
            'replies__author', 'replies__author__profile'
        ).order_by('-created_at')
        context['comment_form'] = CommentForm()
        context['title'] = f'Комментарии к посту: {post.title or "Без названия"}'
        return context


class ReplyCreateView(LoginRequiredMixin, CreateView):
    """Ответ на комментарий"""
    model = Comment
    form_class = CommentForm
    template_name = 'coverse_app/post_comments.html'

    def form_valid(self, form):
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_pk'])
        form.instance.author = self.request.user
        form.instance.parent = get_object_or_404(Comment, pk=self.kwargs['comment_pk'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('coverse_app:post_comments', kwargs={'post_pk': self.kwargs['post_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = get_object_or_404(Post, pk=self.kwargs['post_pk'])
        context['post'] = post
        context['project'] = post.section.project
        context['section'] = post.section
        context['comments'] = post.comments.filter(parent__isnull=True).select_related(
            'author', 'author__profile'
        ).prefetch_related(
            'replies__author', 'replies__author__profile'
        ).order_by('-created_at')
        context['comment_form'] = CommentForm()
        context['title'] = f'Комментарии к посту: {post.title or "Без названия"}'
        return context


class PostCommentsView(DetailView):
    """Страница комментариев к посту"""
    model = Post
    template_name = 'coverse_app/post_comments.html'
    context_object_name = 'post'
    pk_url_kwarg = 'post_pk'

    def get_queryset(self):
        return Post.objects.select_related('section__project__author')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object

        # Загружаем только корневые комментарии (без родителя)
        comments = post.comments.filter(parent__isnull=True).select_related(
            'author', 'author__profile'
        ).prefetch_related(
            'replies__author', 'replies__author__profile'
        ).order_by('-created_at')

        context['comments'] = comments
        context['comment_form'] = CommentForm()
        context['title'] = f'Комментарии к посту: {post.title or "Без названия"}'
        context['project'] = post.section.project
        context['section'] = post.section
        return context


# ===== МОДЕРАЦИЯ КОММЕНТАРИЕВ =====

@superuser_required
def hide_comment_with_reason(request, comment_id):
    """Скрытие комментария с указанием причины"""
    comment = get_object_or_404(Comment, id=comment_id)

    if request.method == 'POST':
        form = ModerationReasonForm(request.POST)
        if form.is_valid():
            # Скрываем комментарий
            comment.is_deleted = True
            comment.deleted_at = timezone.now()
            comment.deleted_by_moderation = True
            comment.deleted_reason = form.cleaned_data['reason']
            comment.save()

            # Логируем действие
            ModerationLog.objects.create(
                moderator=request.user,
                action='hide_post',
                post=comment.post,
                reason=f"Скрыт комментарий #{comment.id}: {form.cleaned_data['reason']}"
            )

            messages.success(request, "Комментарий скрыт модерацией.")
            return HttpResponseRedirect(
                reverse('coverse_app:post_comments', kwargs={'post_pk': comment.post.id})
            )
    else:
        form = ModerationReasonForm()

    return render(request, 'admin_panel/moderation_form.html', {
        'form': form,
        'title': f'Скрыть комментарий',
        'action_url': reverse('admin_panel:hide_comment_with_reason', kwargs={'comment_id': comment_id}),
        'cancel_url': reverse('coverse_app:post_comments', kwargs={'post_pk': comment.post.id}),
    })



