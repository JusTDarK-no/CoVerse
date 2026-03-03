# coverse_app/admin.py
from django.contrib import admin
from django.contrib.auth.models import User
from .models import Tag, Project, Section, Post, Suggestion, ContributionCredit

# ————————————————————————————————————————————————
# РЕГИСТРАЦИЯ МОДЕЛЕЙ
# ————————————————————————————————————————————————

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    readonly_fields = ['slug']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'privacy', 'created_at']
    list_filter = ['status', 'privacy', 'tags']
    search_fields = ['title', 'description', 'author__username']
    filter_horizontal = ['tags']  # для ManyToMany
    date_hierarchy = 'created_at'
    ordering = ['-created_at']


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['project', 'section_type', 'title', 'order', 'description_short']
    list_filter = ['section_type', 'project']
    search_fields = ['title', 'description', 'project__title']
    ordering = ['project', 'order']

    # Показываем description в списке, но укороченно
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description

    description_short.short_description = "Описание"


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'section', 'status', 'created_at']
    list_filter = ['status', 'section__project']
    search_fields = ['title', 'content']
    ordering = ['-created_at']


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display = ['post', 'author', 'status', 'visibility', 'created_at']
    list_filter = ['status', 'visibility', 'post__section__project']
    search_fields = ['suggestion_text', 'author__username']
    readonly_fields = ['created_at', 'reviewed_at']
    actions = ['mark_as_reviewed', 'mark_as_accepted', 'mark_as_rejected']

    def mark_as_reviewed(self, request, queryset):
        queryset.update(status='reviewed', reviewed_at=models.functions.Now())
    mark_as_reviewed.short_description = "Отметить как рассмотренное"

    def mark_as_accepted(self, request, queryset):
        queryset.update(status='accepted')
    mark_as_accepted.short_description = "Принять"

    def mark_as_rejected(self, request, queryset):
        queryset.update(status='rejected')
    mark_as_rejected.short_description = "Отклонить"


@admin.register(ContributionCredit)
class ContributionCreditAdmin(admin.ModelAdmin):
    list_display = ['project', 'contributor', 'credit_type', 'description', 'created_at']
    list_filter = ['credit_type', 'project']
    search_fields = ['contributor__username', 'project__title']
    readonly_fields = ['created_at']