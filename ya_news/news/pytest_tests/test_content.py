from http import HTTPStatus

import pytest
from pytest_lazyfixture import lazy_fixture
from django.conf import settings

from news.forms import CommentForm


@pytest.mark.django_db
@pytest.mark.usefixtures('news_list')
def test_news_count(home_url, client):
    """Количество новостей на главной странице — не более 10."""
    response = client.get(home_url)
    assert 'object_list' in response.context
    object_list = response.context['object_list']
    news_count = object_list.count()
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
@pytest.mark.usefixtures('news_list')
def test_news_order(client, home_url):
    """
    Новости отсортированы от самой свежей к самой старой.
    Свежие новости в начале списка.
    """
    response = client.get(home_url)
    assert 'object_list' in response.context
    object_list = response.context['object_list']
    dates = [news.date for news in object_list]
    assert dates == sorted(dates, reverse=True)


@pytest.mark.django_db
@pytest.mark.usefixtures('news_list')
def test_comments_order(client, detail_url):
    """
    Комментарии на странице отдельной новости отсортированы в хронологическом
    порядке: старые в начале списка, новые — в конце.
    """
    response = client.get(detail_url)
    assert response.status_code == HTTPStatus.OK
    assert 'object' in response.context
    news_obj = response.context['object']
    all_comments = list(news_obj.comment_set.all())
    all_timestamps = [c.created for c in all_comments]
    expected_sorted_timestamps = sorted(all_timestamps)
    assert all_timestamps == expected_sorted_timestamps


@pytest.mark.parametrize(
    'parametrized_client, should_have_form',
    (
        (lazy_fixture('client'), False),
        (lazy_fixture('author_client'), True)
    ),
)
@pytest.mark.django_db
def test_anonymous_client_has_no_form(parametrized_client, should_have_form,
                                      detail_url):
    """
    Анонимному пользователю недоступна форма для отправки комментария
    на странице отдельной новости, а авторизованному доступна.
    """
    response = parametrized_client.get(detail_url)
    assert ('form' in response.context) == should_have_form
    if should_have_form:
        assert isinstance(response.context['form'], CommentForm)
