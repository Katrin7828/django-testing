from pytest_django.asserts import assertRedirects

from django.urls import reverse

from news.models import Comment
from news.forms import BAD_WORDS

import pytest

from http import HTTPStatus


COMMENT_TEXT = 'Текст комментария'
NEW_COMMENT_TEXT = 'Обновлённый комментарий'


@pytest.mark.django_db
def test_user_can_create_comment(client, news, author):
    """Авторизованный пользователь может отправить комментарий."""
    url = reverse('news:detail', args=(news.pk,))
    client.force_login(author)
    form_data = {'text': COMMENT_TEXT}
    response = client.post(url, data=form_data)
    assertRedirects(response, f'{url}#comments')
    comments_count = Comment.objects.count()
    assert comments_count == 1
    comment = Comment.objects.get()
    assert comment.text == COMMENT_TEXT
    assert comment.news == news
    assert comment.author == author


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, news):
    """Анонимный пользователь не может отправить комментарий."""
    url = reverse('news:detail', args=(news.pk,))
    form_data = {'text': COMMENT_TEXT}
    client.post(url, data=form_data)
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_user_cant_use_bad_words(news, author_client):
    """
    Если комментарий содержит запрещённые слова, он не будет опубликован,
    а форма вернёт ошибку.
    """
    url = reverse('news:detail', args=(news.pk,))
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = author_client.post(url, data=bad_words_data)
    assert response.status_code == HTTPStatus.OK
    form = response.context.get('form')
    assert form is not None
    assert 'text' in form.errors
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_author_can_edit_comment(author_client, author, news):
    """
    Авторизованный пользователь может редактировать
    или удалять свои комментарии.
    """
    news_url = reverse('news:detail', args=(news.pk,))
    url_to_comments = news_url + '#comments'
    comment = Comment.objects.create(
        news=news,
        author=author,
        text=COMMENT_TEXT,
    )
    edit_url = reverse('news:edit', args=(comment.pk,))
    delete_url = reverse('news:delete', args=(comment.pk,))
    form_data = {'text': NEW_COMMENT_TEXT}
    response = author_client.post(edit_url, data=form_data)
    assertRedirects(response, url_to_comments)
    comment.refresh_from_db()
    assert comment.text == NEW_COMMENT_TEXT
    response = author_client.delete(delete_url, data=form_data)
    assertRedirects(response, url_to_comments)
    assert response.status_code == HTTPStatus.FOUND
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_other_user_cant_edit_comment(author, not_author_client, news):
    """
    Авторизованный пользователь не может редактировать
    или удалять чужие комментарии.
    """
    comment = Comment.objects.create(
        news=news,
        text=COMMENT_TEXT,
        author=author,
    )
    form_data = {'text': NEW_COMMENT_TEXT}
    edit_url = reverse('news:edit', args=(comment.pk,))
    delete_url = reverse('news:delete', args=(comment.pk,))
    response = not_author_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_count = Comment.objects.count()
    assert comments_count == 1
    response = not_author_client.post(edit_url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == COMMENT_TEXT
