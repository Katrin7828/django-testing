from http import HTTPStatus

import pytest
from pytest_django.asserts import assertRedirects, assertFormError

from news.models import Comment
from news.forms import BAD_WORDS, WARNING


@pytest.mark.django_db
def test_user_can_create_comment(news, author, author_client, comment_text_new,
                                 detail_url, detail_comments):
    """Авторизованный пользователь может отправить комментарий."""
    response = author_client.post(detail_url, data=comment_text_new)
    assertRedirects(response, detail_comments)
    comments_count = Comment.objects.count()
    assert comments_count == 1
    comment = Comment.objects.get()
    assert comment.text == comment_text_new['text']
    assert comment.news == news
    assert comment.author == author


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, detail_url,
                                            comment_text_new):
    """Анонимный пользователь не может отправить комментарий."""
    client.post(detail_url, data=comment_text_new)
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_user_cant_use_bad_words(author_client, detail_url):
    """
    Если комментарий содержит запрещённые слова, он не будет опубликован,
    а форма вернёт ошибку.
    """
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = author_client.post(detail_url, data=bad_words_data)
    assert response.status_code == HTTPStatus.OK
    assertFormError(
        response.context['form'],
        'text',
        WARNING,
    )
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_author_can_edit_comment(author_client, detail_url, edit_url,
                                 comment_text_new, comment, detail_comments):
    """Авторизованный пользователь может редактировать свои комментарии."""
    response = author_client.post(edit_url, data=comment_text_new)
    assertRedirects(response, detail_comments)
    comment.refresh_from_db()
    assert comment.text == comment_text_new['text']


@pytest.mark.django_db
def test_author_can_delete_comment(author_client, delete_url,
                                   comment_text_new, detail_comments):
    """Авторизованный пользователь может удалять свои комментарии."""
    response = author_client.delete(delete_url, data=comment_text_new)
    assertRedirects(response, detail_comments)
    assert response.status_code == HTTPStatus.FOUND
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_other_user_cant_edit_comment(admin_client, comment, edit_url,
                                      comment_text_new):
    """Авторизованный пользователь не может редактировать чужие комментарии."""
    original_text = comment.text
    response = admin_client.post(edit_url, data=comment_text_new)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment_from_db = Comment.objects.get(pk=comment.pk)
    assert comment_from_db.text == original_text


@pytest.mark.django_db
def test_other_user_cant_delete_comment(admin_client, delete_url,
                                        comment_text_new):
    """Авторизованный пользователь не может редактировать чужие комментарии."""
    response = admin_client.post(delete_url, data=comment_text_new)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_count = Comment.objects.count()
    assert comments_count == 1
