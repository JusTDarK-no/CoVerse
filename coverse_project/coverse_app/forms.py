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