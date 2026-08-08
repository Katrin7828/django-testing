from http import HTTPStatus

from django.urls import reverse

import pytest

from django.test import Client


@pytest.mark.django_db
def test_home_availability_for_anonymous_user(client):
    """Анонимному пользователю доступна главная страница."""
    url = reverse('news:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_single_news_page_availability_for_anonymous(client, news):
    """Может ли анонимный пользователь открыть страницу конкретной новости?"""
    url = reverse('news:detail', args=(news.pk,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize('name', ('news:edit', 'news:delete'))
@pytest.mark.django_db
def test_comments_availability_for_author(name, comment):
    """Проверяем доступ к страницам редактирования и удаления комментариев."""
    author = comment.author
    client = Client()
    client.force_login(author)
    url = reverse(name, args=(comment.pk,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize('name', ('news:edit', 'news:delete'))
@pytest.mark.django_db
def test_comments_availability_for_anonymous(name, comment):
    """Аноним не может редактировать и удалять комментарии."""
    client = Client()
    url = reverse(name, args=(comment.pk,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.FOUND


@pytest.mark.parametrize('name', ('news:edit', 'news:delete'))
@pytest.mark.django_db
def test_other_user_cannot_edit_and_delete_comment(name, comment, other_user):
    """Неавтор не может редактировать и удалять комментарии."""
    client = Client()
    client.force_login(other_user)
    url = reverse(name, args=(comment.pk,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.parametrize('name, expected_status', [
    ('users:login', HTTPStatus.OK),
    ('users:signup', HTTPStatus.OK),
    ('users:logout', HTTPStatus.METHOD_NOT_ALLOWED),
])
@pytest.mark.django_db
def test_auth_pages_behavior(client, name, expected_status):
    """Доступ регистрации, входа и выхода для анонима."""
    url = reverse(name)
    response = client.get(url)
    assert response.status_code == expected_status
