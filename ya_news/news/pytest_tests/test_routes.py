from http import HTTPStatus

from django.urls import reverse

import pytest
from pytest_django.asserts import assertRedirects


@pytest.mark.django_db
def test_pages_availability(client, news):
    """
    Главная страница и страница отдельной новости
    доступны анонимному пользователю.
    """
    urls = [
        ('news:home', None),
        ('news:detail', (news.pk,)),
    ]
    for name, args in urls:
        url = reverse(name, args=args)
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_availability_for_comment_edit_and_delete(client, comment, author,
                                                  other_user):
    """
    Страницы удаления и редактирования комментария
    доступны автору комментария, но недоступны другому пользователю (404).
    """
    urls = [
        (author, 'news:edit', (comment.pk,), HTTPStatus.OK),
        (author, 'news:delete', (comment.pk,), HTTPStatus.OK),
        (other_user, 'news:edit', (comment.pk,), HTTPStatus.NOT_FOUND),
        (other_user, 'news:delete', (comment.pk,), HTTPStatus.NOT_FOUND),
    ]
    for user, name, args, expected_status in urls:
        client.force_login(user)
        url = reverse(name, args=args)
        response = client.get(url)
        assert response.status_code == expected_status


@pytest.mark.django_db
def test_redirect_for_anonymous_client(client, comment):
    """
    При попытке перейти на страницу редактирования или удаления комментария
    анонимный пользователь перенаправляется на страницу авторизации.
    """
    login_url = reverse('users:login')
    urls = [
        ('news:edit', (comment.pk,)),
        ('news:delete', (comment.pk,))
    ]
    for name, args in urls:
        url = reverse(name, args=args)
        expected_url = f'{login_url}?next={url}'
        response = client.get(url)
        assertRedirects(response, expected_url)


@pytest.mark.django_db
def test_auth_pages_behavior(client, comment):
    """
    Страницы регистрации пользователей,
    входа в учётную запись и выхода из неё доступны анонимным пользователям.
    """
    urls = (
        ('news:home', None),
        ('news:detail', (comment.id,)),
        ('users:login', None),
        ('users:signup', None),
    )
    for name, args in urls:
        url = reverse(name, args=args)
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK
