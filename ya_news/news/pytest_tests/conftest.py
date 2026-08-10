import pytest

from django.contrib.auth import get_user_model

from news.models import News, Comment

User = get_user_model()


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
def other_user():
    """Неавтор."""
    return User.objects.create_user(username='other_user',
                                    password='password')


@pytest.fixture
def news_setup(db):
    user = User.objects.create_user(username='1', password='123')
    news = News.objects.create(
        title="Тест",
        text="Текст",
    )
    return user, news


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def author_client(author, client):
    """Пользователь, который будет автором комментария."""
    client.force_login(author)
    return client


@pytest.fixture
def comment_author_client(comment, client):
    """Клиент, залогиненный под автором этого комментария."""
    client.force_login(comment.author)
    return client


@pytest.fixture
def not_author_client(client, django_user_model):
    """Клиент, который не является автором заметки."""
    other_user = django_user_model.objects.create_user(
        username='other_user',
        password='123'
    )
    client.force_login(other_user)
    return client
