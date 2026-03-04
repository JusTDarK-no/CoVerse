# coverse_app/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import *
from django.core.exceptions import ValidationError

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Электронная почта")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        labels = {
            'username': 'Имя пользователя',
            'password1': 'Пароль',
            'password2': 'Подтверждение пароля',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class MultipleImageField(forms.FileField):
    """Поле для загрузки нескольких изображений"""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", forms.ClearableFileInput(attrs={'multiple': True}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class PostForm(forms.ModelForm):
    """Форма для поста БЕЗ поля изображений (обрабатываем вручную)"""

    class Meta:
        model = Post
        fields = ['title', 'content', 'status']


from django import forms
from .models import ModerationLog

class ModerationReasonForm(forms.ModelForm):
    """Форма для указания причины модерации"""
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'form-control',
            'placeholder': 'Укажите причину действия...',
            'required': 'required'
        }),
        label="Причина",
        max_length=500
    )

    class Meta:
        model = ModerationLog
        fields = ['reason']


class UserBlockReasonForm(forms.Form):
    """Форма для указания причины блокировки пользователя"""
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'form-control',
            'placeholder': 'Укажите причину блокировки...',
            'required': 'required'
        }),
        label="Причина блокировки",
        max_length=500
    )

class CommentForm(forms.ModelForm):
    """Форма для создания комментария"""
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Напишите комментарий...',
            'required': 'required'
        }),
        label="Текст комментария",
        max_length=1000
    )

    class Meta:
        model = Comment
        fields = ['content']


# ============================================================================
# ДОБАВИТЬ В КОНЕЦ forms.py ПОСЛЕ CommentForm
# ============================================================================

class SuggestionForm(forms.ModelForm):
    """Форма создания предложения"""

    class Meta:
        model = Suggestion
        fields = ['suggestion_text', 'suggestion_type', 'visibility', 'original_excerpt']
        widgets = {
            'suggestion_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Опишите ваше предложение...'
            }),
            'suggestion_type': forms.Select(attrs={'class': 'form-control'}),
            'visibility': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'original_excerpt': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Цитата из поста (необязательно)'
            }),
        }


class SuggestionAttachmentForm(forms.Form):
    """Форма для загрузки вложений к предложению"""
    attachments = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*,.pdf,.doc,.docx,.txt'
        }),
        required=False,
        label="Прикрепить файлы (до 5)"
    )


class SuggestionResponseForm(forms.Form):
    """Форма ответа на предложение (Принять/Отклонить)"""
    ACTION_CHOICES = [
        ('accept', 'Принять'),
        ('reject', 'Отклонить'),
    ]
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Действие"
    )
    rejection_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Причина отказа (необязательно)'
        }),
        required=False,
        label="Причина отказа"
    )


class PostEditWithSuggestionForm(forms.ModelForm):
    """Форма редактирования поста с привязкой к предложению"""
    change_summary = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Краткое описание изменений (необязательно)'
        }),
        required=False,
        label="Описание изменений"
    )

    class Meta:
        model = Post
        fields = ['title', 'content', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }