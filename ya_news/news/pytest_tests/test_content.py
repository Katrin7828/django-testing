import pytest

from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from datetime import datetime, timedelta

from ..models import News, Comment
from news.forms import CommentForm

from http import HTTPStatus

User = get_user_model()


@pytest.mark.django_db
def test_news_count(client):
    """Количество новостей на главной странице — не более 10."""
    for i in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1):
        News.objects.create(
            title=f'Заголовок {i}',
            text=f'Текст {i}',
        )
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    news_count = object_list.count()
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(client):
    """
    Новости отсортированы от самой свежей к самой старой.
    Свежие новости в начале списка.
    """
    today = datetime.today()
    created_news = []
    for index in range(settings.NEWS_COUNT_ON_HOME_PAGE):
        date = today - timedelta(days=index)
        note = News.objects.create(
            title='Новость {index}',
            text='Текст новости',
            date=date,
        )
        created_news.append(note)
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    assert list(object_list) == created_news


@pytest.mark.django_db
def test_comments_order(client, news_setup):
    """
    Комментарии на странице отдельной новости отсортированы в хронологическом
    порядке: старые в начале списка, новые — в конце.
    """
    now = timezone.now()
    author, news = news_setup
    client.force_login(author)
    created_comments = []
    for i in range(settings.NEWS_COUNT_ON_HOME_PAGE):
        comment = Comment.objects.create(
            news=news,
            author=author,
            text=f'Tекст {i}',
        )
        Comment.objects.filter(pk=comment.pk).update(
            created=now + timedelta(days=i))
        created_comments.append(comment)
    detail_url = reverse('news:detail', args=(news.pk,))
    response = client.get(detail_url)
    assert response.status_code == HTTPStatus.OK
    news_obj = response.context['object']
    all_comments = list(news_obj.comment_set.all())
    all_timestamps = [c.created for c in all_comments]
    expected_sorted_timestamps = sorted(all_timestamps)
    assert all_timestamps == expected_sorted_timestamps


@pytest.mark.django_db
def test_anonymous_client_has_no_form(client, news_setup):
    """
    Анонимному пользователю недоступна форма для отправки комментария
    на странице отдельной новости, а авторизованному доступна.
    """
    author, news = news_setup
    url = reverse('news:detail', args=(news.pk,))
    response = client.get(url)
    assert 'form' not in response.context
    client.force_login(author)
    response = client.get(url)
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
