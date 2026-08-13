from http import HTTPStatus

import pytest
from pytest_django.asserts import assertRedirects
from pytest_lazyfixture import lazy_fixture


@pytest.mark.django_db
@pytest.mark.parametrize(
    'client_fixture, status',
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
def test_availability_for_comment_edit_and_delete(client_fixture, url, status):
    """
    Страницы удаления и редактирования комментария
    доступны автору комментария, но недоступны другому пользователю (404).
    """
    response = client_fixture.get(url)
    assert response.status_code == status


@pytest.mark.django_db
@pytest.mark.parametrize(
    'url, redirect_url',
    (
        (lazy_fixture('edit_url'), lazy_fixture('login_redirect_for_edit')),
        (lazy_fixture('delete_url'),
         lazy_fixture('login_redirect_for_delete')),
    )
)
def test_redirect_for_anonymous_client(client, url, redirect_url):
    """
    При попытке перейти на страницу редактирования или удаления комментария
    анонимный пользователь перенаправляется на страницу авторизации.
    """
    response = client.get(url)
    assertRedirects(response, redirect_url)


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
