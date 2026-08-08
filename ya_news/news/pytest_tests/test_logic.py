from pytest_django.asserts import assertRedirects, assertFormError

from django.urls import reverse
from django.contrib.auth import get_user_model

from news.models import Comment, News
from news.forms import BAD_WORDS, WARNING

import pytest

from http import HTTPStatus

def test_user_can_create_comment(client, news):
    """Авторизованный пользователь может создать комментарий."""
    User = get_user_model()
    author = User.objects.create_user(username='test_author', password='123')
    client.force_login(author)
    comment = {'text': 'Новый комментарий.'}
    url = reverse('news:detail', args=(news.pk,))
    response = client.post(url, data=comment)
    expected_url = reverse('news:detail', args=(news.pk,)) + '#comments'
    assertRedirects(response, expected_url)
    assert Comment.objects.count() == 1
    new_comment = Comment.objects.get()
    assert new_comment.text == comment['text']
    assert new_comment.author == author
    assert new_comment.news == news


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, news):
    """Анонимный пользователь не может создавать комментарии."""
    url = reverse('news:detail', args=(news.pk,))
    comment = {'text': 'Новый комментарий.'}
    response = client.post(url, data=comment)
    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={url}'
    assertRedirects(response, expected_url)
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_bad_words(news, author_client):
    """Если комментарий содержит запрещённые слова, он не будет опубликован."""
    url = reverse('news:detail', args=(news.pk,))
    bad_word = f'Какой-то текст, {BAD_WORDS[0]}, еще текст'
    response = author_client.post(url, data={'text': bad_word})
    assert response.status_code == HTTPStatus.OK
    form = response.context.get('form')
    assert form is not None
    assert 'text' in form.errors
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_author_can_edit_comment(comment_author_client, comment, news):
    """Автор может редактировать свои комментарии."""
    updated_data = {'text': 'Это обновлённый текст комментария.'}
    url = reverse('news:edit', args=(comment.pk,))
    response = comment_author_client.post(url, data=updated_data)
    expected_url = reverse('news:detail', args=(news.pk,)) + '#comments'
    assertRedirects(response, expected_url)
    comment.refresh_from_db()
    assert comment.text == updated_data['text']
    assert comment.author == comment.author
    assert comment.news == news


def test_other_user_cant_edit_comment(not_author_client, comment):
    """Другие пользователи не могут редактировать не свои комментарии."""
    updated_data = {'text': 'Это обновлённый текст комментария.'}
    url = reverse('news:edit', args=(comment.pk,))
    response = not_author_client.post(url, data=updated_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text != updated_data['text']
    assert comment.author == comment.author


def test_author_can_delete_comment(comment_author_client, slug_for_args, news):
    """Автор может удалять свой комментарий."""
    url = reverse('news:delete', args=(slug_for_args,))
    response = comment_author_client.post(url)
    expected_url = reverse('news:detail', args=(news.pk,)) + '#comments'
    assertRedirects(response, expected_url)
    assert Comment.objects.count() == 0


def test_other_user_cant_delete_comment(not_author_client, slug_for_args):
    """Другие авторы не могут удалять чужие комментарии."""
    comments_count = Comment.objects.count()
    url = reverse('news:delete', args=(slug_for_args,))
    response = not_author_client.delete(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_count_after = Comment.objects.count()
    assert comments_count == comments_count_after
