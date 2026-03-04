# coverse_app/models.py
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from django.core.exceptions import ValidationError
import os
from django.utils import timezone

# ————————————————————————————————————————————————
# ПОМОЩНИКИ / УТИЛИТЫ
# ————————————————————————————————————————————————

def upload_to(instance, filename):
    """Утилита для загрузки файлов: project_{id}/filename"""
    return os.path.join(
        f'project_{instance.project.id}',
        slugify(instance.project.title)[:30],
        filename
    )


# ————————————————————————————————————————————————
# МОДЕЛИ
# ————————————————————————————————————————————————

class Tag(models.Model):
    """Теги для классификации проектов (жанр, тема, настроение)"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Название")
    # Заменяем SlugField на CharField для поддержки кириллицы
    slug = models.CharField(
        max_length=60,
        unique=True,
        blank=True,
        editable=False,
        verbose_name="Слаг"
    )

    class Meta:
        ordering = ['name']
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name

    def clean(self):
        """Валидация перед сохранением"""
        if not self.name or not self.name.strip():
            raise ValidationError({"name": "Название тега не может быть пустым."})

    def save(self, *args, **kwargs):
        self.full_clean()  # Запускаем валидацию
        if not self.slug:
            # allow_unicode=True разрешает кириллицу в слаге
            self.slug = slugify(self.name.strip(), allow_unicode=True)
        super().save(*args, **kwargs)


class Project(models.Model):
    """Основной контейнер творческого проекта"""
    PRIVACY_CHOICES = [
        ('public', 'Публичный'),
        ('unlisted', 'По ссылке'),
        ('private', 'Только я'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('in_progress', 'В разработке'),
        ('completed', 'Завершён'),
    ]

    def upload_to_project_cover(instance, filename):
        """Для обложки проекта: project_<id>/title/filename"""
        return os.path.join(
            f'project_{instance.id}',
            slugify(instance.title)[:30],
            filename
        )

    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(max_length=1000, verbose_name="Описание")
    cover_image = models.ImageField(
        upload_to=upload_to_project_cover,  # ← теперь правильно!
        null=True,
        blank=True,
        verbose_name="Обложка"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_projects',
        verbose_name="Автор"
    )
    privacy = models.CharField(
        max_length=20,
        choices=PRIVACY_CHOICES,
        default='public',
        verbose_name="Доступность"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Статус"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='projects', verbose_name="Теги")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлён")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"

    MODERATION_STATUS_CHOICES = [
        ('active', 'Активен'),
        ('hidden_by_moderation', 'Скрыт модерацией'),
    ]

    moderation_status = models.CharField(
        max_length=30,
        choices=MODERATION_STATUS_CHOICES,
        default='active',
        verbose_name="Статус модерации"
    )
    moderation_hidden_at = models.DateTimeField(null=True, blank=True, verbose_name="Скрыт модерацией")

    def __str__(self):
        return f"{self.title} — {self.author.username}"

    def get_absolute_url(self):
        return reverse('project_detail', kwargs={'pk': self.pk})


class Section(models.Model):
    """Раздел внутри проекта: может быть несколько секций одного типа (например, «Сюжет» × 2)"""
    SECTION_TYPES = [
        ('plot', 'Сюжет'),
        ('world', 'Мир'),
        ('characters', 'Персонажи'),
        ('concepts', 'Концепты'),
        ('art', 'Искусство'),
        ('other', 'Прочее'),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='sections',
        verbose_name="Проект"
    )
    title = models.CharField(max_length=100, verbose_name="Заголовок раздела")
    section_type = models.CharField(
        max_length=20,
        choices=SECTION_TYPES,
        verbose_name="Тип раздела"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    # Дополнительно: можно добавить описание, если нужно
    description = models.TextField(max_length=300, blank=True, verbose_name="Описание")

    class Meta:
        ordering = ['order']
        # УБРАЛИ unique_together — теперь допускаются дубли по типу!
        verbose_name = "Раздел"
        verbose_name_plural = "Разделы"

    def __str__(self):
        # Показываем тип + заголовок, но не скрываем дубли
        return f"{self.get_section_type_display()}: {self.title}"

    def clean(self):
        """Опционально: валидация на уровне модели (например, запретить пустой заголовок при определённых типах)"""
        if not self.title.strip():
            raise ValidationError("Заголовок раздела не может быть пустым.")

class Post(models.Model):
    """Блок контента: описание мира, биография персонажа и т.д."""
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликован'),
    ]
    moderation_deleted = models.BooleanField(default=False, verbose_name="Удалён модерацией")
    moderation_deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата удаления модерацией")

    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name="Раздел"
    )
    title = models.CharField(max_length=200, blank=True, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Статус"
    )
    is_deleted = models.BooleanField(default=False, verbose_name="Удалён (скрыт)")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата удаления")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлён")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Пост"
        verbose_name_plural = "Посты"

    def __str__(self):
        return self.title or f"Пост #{self.id} в «{self.section.title}»"

    def delete(self, *args, **kwargs):
        """Переопределяем delete() — теперь только скрытие"""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])


class ContributionCredit(models.Model):
    """Фиксация вклада участника в проект (соавторство, иллюстрация и т.д.)"""
    CREDIT_TYPE_CHOICES = [
        ('suggestion_accepted', 'Принятое предложение'),
        ('co_author', 'Соавторство'),
        ('artwork', 'Иллюстрация'),
        ('editing', 'Редактура'),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='credits',
        verbose_name="Проект"
    )
    contributor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contributions',
        verbose_name="Участник"
    )
    credit_type = models.CharField(
        max_length=30,
        choices=CREDIT_TYPE_CHOICES,
        verbose_name="Тип вклада"
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Описание вклада"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата")

    class Meta:
        unique_together = ['project', 'contributor', 'credit_type', 'description']
        verbose_name = "Вклад"
        verbose_name_plural = "Вклады"

    def __str__(self):
        return f"{self.contributor.username} → {self.project.title} ({self.get_credit_type_display()})"


def post_image_upload_to(instance, filename):
    """Путь для загрузки: project_{id}/posts/post_{post_id}/filename"""
    return os.path.join(
        f'project_{instance.post.section.project.id}',
        'posts',
        f'post_{instance.post.id}',
        filename
    )

class PostImage(models.Model):
    """Изображения, прикреплённые к посту"""
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name="Пост"
    )
    image = models.ImageField(
        upload_to=post_image_upload_to,
        verbose_name="Изображение"
    )
    caption = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Подпись (опционально)"
    )
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Изображение к посту"
        verbose_name_plural = "Изображения к посту"

    def __str__(self):
        return f"Изображение {self.id} для поста {self.post.id}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_blocked = models.BooleanField(default=False, verbose_name="Заблокирован")
    blocked_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата блокировки")

    def __str__(self):
        return f"Профиль {self.user.username}"

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


class ModerationLog(models.Model):
    """Лог всех действий модерации"""
    ACTION_CHOICES = [
        ('hide_project', 'Скрытие проекта'),
        ('unhide_project', 'Восстановление проекта'),
        ('hide_post', 'Скрытие поста'),
        ('block_user', 'Блокировка пользователя'),
        ('unblock_user', 'Разблокировка пользователя'),
    ]

    moderator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='moderation_actions',
        verbose_name="Модератор"
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES, verbose_name="Действие")

    # Связанные объекты (один из них будет заполнен)
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderation_logs',
        verbose_name="Проект"
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderation_logs',
        verbose_name="Пост"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderation_logs',
        verbose_name="Пользователь"
    )

    reason = models.TextField(verbose_name="Причина")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата действия")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Лог модерации"
        verbose_name_plural = "Логи модерации"

    def __str__(self):
        return f"{self.get_action_display()} — {self.created_at.strftime('%d.%m.%Y %H:%M')}"


class Comment(models.Model):
    """Комментарии к постам"""
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Пост"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Автор"
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies',
        verbose_name="Родительский комментарий"
    )
    content = models.TextField(verbose_name="Текст комментария")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлён")

    # Модерация
    is_deleted = models.BooleanField(default=False, verbose_name="Удалён")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата удаления")
    deleted_by_moderation = models.BooleanField(default=False, verbose_name="Удалён модерацией")
    deleted_reason = models.TextField(null=True, blank=True, verbose_name="Причина удаления")

    class Meta:
        ordering = ['created_at']
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self):
        return f"Комментарий #{self.id} от {self.author.username}"

    def get_truncated_content(self, max_length=200):
        """Возвращает обрезанный текст комментария"""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + '...'

    @property
    def has_replies(self):
        """Проверяет, есть ли ответы на комментарий"""
        return self.replies.exists()

    @property
    def is_truncated(self):
        """Проверяет, нужно ли обрезать комментарий"""
        return len(self.content) > 200

class Suggestion(models.Model):
    """Предложение от участника для улучшения поста"""
    VISIBILITY_CHOICES = [
        ('author_only', 'Только автору'),
        ('public', 'Публичное'),
    ]
    STATUS_CHOICES = [
        ('new', 'Новое'),
        ('reviewed', 'Рассмотрено'),
        ('accepted', 'Принято'),
        ('rejected', 'Отклонено'),
    ]
    SUGGESTION_TYPE_CHOICES = [
        ('correction', 'Исправление'),
        ('new_idea', 'Новая идея'),
        ('other', 'Другое'),
    ]

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='suggestions',
        verbose_name="Пост"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='suggestions_made',
        verbose_name="Автор предложения"
    )
    original_excerpt = models.TextField(
        blank=True,
        verbose_name="Цитата из поста (для контекста)"
    )
    suggestion_text = models.TextField(verbose_name="Предложение")
    suggestion_type = models.CharField(
        max_length=20,
        choices=SUGGESTION_TYPE_CHOICES,
        default='other',
        verbose_name="Тип предложения"
    )
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default='public',
        verbose_name="Видимость"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="Статус"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Прочитано автором")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="Рассмотрено")
    rejection_reason = models.TextField(
        blank=True,
        verbose_name="Причина отказа"
    )
    accepted_post_version = models.ForeignKey(
        'PostEditLog',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_suggestions',
        verbose_name="Версия поста после принятия"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Предложение"
        verbose_name_plural = "Предложения"

    def __str__(self):
        return f"Предложение от {self.author.username} к «{self.post.section.project.title}»"

    def mark_as_read(self):
        """Отметить предложение как прочитанное"""
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])

    def can_view_by_user(self, user):
        """Проверка доступа к предложению"""
        if self.visibility == 'public':
            return True
        post_author = self.post.section.project.author
        return user == post_author or user == self.author

class SuggestionAttachment(models.Model):
    """Файлы, прикреплённые к предложению"""
    suggestion = models.ForeignKey(
        'Suggestion',
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name="Предложение"
    )
    file = models.FileField(
        upload_to='suggestions/',
        verbose_name="Файл"
    )
    file_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Тип файла"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Загружен")

    class Meta:
        ordering = ['uploaded_at']
        verbose_name = "Вложение к предложению"
        verbose_name_plural = "Вложения к предложениям"

    def __str__(self):
        return f"Вложение {self.id} к предложению {self.suggestion.id}"

    def save(self, *args, **kwargs):
        if self.file:
            ext = os.path.splitext(self.file.name)[1].lower()
            self.file_type = ext
        super().save(*args, **kwargs)


class PostEditLog(models.Model):
    """Лог изменений поста (для отслеживания вклада)"""
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='edit_logs',
        verbose_name="Пост"
    )
    editor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='post_edits',
        verbose_name="Редактор"
    )
    suggestion = models.ForeignKey(
        'Suggestion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='post_edit_logs',
        verbose_name="Предложение (инициатор)"
    )
    old_content = models.TextField(
        verbose_name="Старое содержание",
        editable=False
    )
    new_content = models.TextField(
        verbose_name="Новое содержание",
        editable=False
    )
    old_title = models.CharField(
        max_length=200,
        verbose_name="Старый заголовок",
        editable=False
    )
    new_title = models.CharField(
        max_length=200,
        verbose_name="Новый заголовок",
        editable=False
    )
    edited_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата изменения")
    change_summary = models.TextField(
        blank=True,
        verbose_name="Описание изменений"
    )

    class Meta:
        ordering = ['-edited_at']
        verbose_name = "Лог изменения поста"
        verbose_name_plural = "Логи изменений постов"

    def __str__(self):
        return f"Изменение поста #{self.post.id} от {self.edited_at}"

