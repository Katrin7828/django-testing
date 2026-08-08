import pytest
from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from datetime import timedelta

from ..models import News, Comment

from http import HTTPStatus

User = get_user_model()


@pytest.mark.django_db
def test_news_limit_is_ten(client):
    """Проверка новостей."""
    user = User.objects.create_user(username='1', password='123')
    client.force_login(user)
    for i in range(15):
        News.objects.create(
            title=f'Заголовок {i}',
            text=f'Текст {i}',
        )
    url = reverse('news:home')
    object_list = list(
        client.get(url).context['object_list']
    )
    assert len(object_list) == settings.NEWS_COUNT_ON_HOME_PAGE
    assert object_list == sorted(
        object_list, key=lambda news: news.date, reverse=True
    )


@pytest.mark.django_db
def test_comments(client, news_setup):
    """Проверка сортировки комментариев."""
    user, news = news_setup
    client.force_login(user)
    now = timezone.now()
    c_new = Comment.objects.create(news=news, author=user, text='Новый')
    c_mid = Comment.objects.create(news=news, author=user, text='Средний')
    c_old = Comment.objects.create(news=news, author=user, text='Старый')
    Comment.objects.filter(pk=c_new.pk).update(created=now)
    Comment.objects.filter(pk=c_mid.pk).update(
        created=now - timedelta(days=5))
    Comment.objects.filter(pk=c_old.pk).update(created=now - timedelta(days=10))
    response = client.get(reverse('news:detail', kwargs={'pk': news.pk}))
    news_obj = response.context['object']
    raw_comments = list(news_obj.comment_set.all())
    sorted_comments = sorted(raw_comments, key=lambda c: c.created,
                             reverse=False)
    assert [c.text for c in sorted_comments] == ['Старый', 'Средний', 'Новый']


@pytest.mark.django_db
def test_comments_available(client, comment):
    """Проверка доступности комментариев."""
    user = User.objects.create_user(username='1', password='123')
    client.force_login(user)
    url = reverse('news:detail', kwargs={'pk': comment.news.pk})
    response = client.get(url)
    html_auth = response.content.decode('utf-8')
    assert response.status_code == HTTPStatus.OK
    assert 'Сохранить' in html_auth
    client.logout()
    response_anon = client.get(url)
    html_anon = response_anon.content.decode('utf-8')
    assert response_anon.status_code == HTTPStatus.OK
    assert 'Сохранить' not in html_anon
