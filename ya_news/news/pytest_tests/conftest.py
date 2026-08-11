from datetime import datetime, timedelta

import pytest
from django.test import Client
from django.conf import settings
from django.urls import reverse

from news.models import News, Comment


@pytest.fixture
def news(db):
    """Cоздаем одну тестовую новость."""
    return News.objects.create(
        title="Тестовая новость для теста",
        text="Это текст тестовой новости.",
    )


@pytest.fixture
def comment(db, news, author):
    """Создаем комментарий, привязанный к новости."""
    return Comment.objects.create(
        text='Текст тестового комментария',
        author=author,
        news=news,
    )


@pytest.fixture
def other_user(django_user_model):
    """Неавтор."""
    return django_user_model.objects.create_user(username='other_user')


@pytest.fixture
def author(django_user_model):
    """Автор."""
    return django_user_model.objects.create_user(username='Автор')


@pytest.fixture
def author_client(author):
    """Пользователь, который будет автором комментария."""
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture
def news_list():
    """Список новостей."""
    return News.objects.bulk_create(
        News(
            title=f'Заголовок {i}',
            text=f'Текст {i}',
            date=datetime.today().date() - timedelta(days=i),
        )
        for i in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    )


@pytest.fixture
def home_url():
    """URL главной страницы."""
    return reverse('news:home')


@pytest.fixture
def detail_url(news):
    """URL страницы новости."""
    return reverse('news:detail', args=(news.pk,))


@pytest.fixture
def delete_url(comment):
    """URL удаления новости."""
    return reverse('news:delete', args=(comment.pk,))


@pytest.fixture
def edit_url(comment):
    """URL редактирования новости."""
    return reverse('news:edit', args=(comment.pk,))


@pytest.fixture
def login_url():
    """URL выхода."""
    return reverse('users:login')


@pytest.fixture
def signup_url():
    """URL регистрации."""
    return reverse('users:signup')


@pytest.fixture
def comment_text_new():
    """Новые текст для комментария."""
    return {'text': 'Новый текст'}
