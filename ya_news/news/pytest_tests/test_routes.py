from http import HTTPStatus

from django.urls import reverse
import pytest
from pytest_django.asserts import assertRedirects
from pytest_lazyfixture import lazy_fixture


@pytest.mark.django_db
@pytest.mark.parametrize(
    'url',
    [
        (lazy_fixture('home_url')),
        (lazy_fixture('detail_url')),
    ]
)
def test_pages_availability(client, url):
    """
    Главная страница и страница отдельной новости
    доступны анонимному пользователю.
    """
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize(
    'user_fixture, status',
    (
        (lazy_fixture('author_client'), HTTPStatus.OK),
        (lazy_fixture('admin_client'), HTTPStatus.NOT_FOUND),
    )
)
@pytest.mark.parametrize(
    'url',
    (
        (lazy_fixture('edit_url')),
        (lazy_fixture('delete_url')),
    )
)
def test_availability_for_comment_edit_and_delete(user_fixture, url, status):
    """
    Страницы удаления и редактирования комментария
    доступны автору комментария, но недоступны другому пользователю (404).
    """
    response = user_fixture.get(url)
    assert response.status_code == status


@pytest.mark.django_db
@pytest.mark.parametrize(
    'url',
    (
        (lazy_fixture('edit_url')),
        (lazy_fixture('delete_url')),
    )
)
def test_redirect_for_anonymous_client(client, url, login_url):
    """
    При попытке перейти на страницу редактирования или удаления комментария
    анонимный пользователь перенаправляется на страницу авторизации.
    """
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'url',
    (
        (lazy_fixture('home_url')),
        (lazy_fixture('detail_url')),
        (lazy_fixture('login_url')),
        (lazy_fixture('signup_url')),
    )
)
def test_auth_pages_behavior(client, url):
    """
    Страницы регистрации пользователей,
    входа в учётную запись и выхода из неё доступны анонимным пользователям.
    """
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
