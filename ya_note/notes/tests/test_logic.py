from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import WARNING

from pytils.translit import slugify

User = get_user_model()


class TestNoteCreation(TestCase):
    NOTE_TEXT = 'Текст'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.auth_user = User.objects.create(username='auth_user')
        cls.auth_user_client = Client()
        cls.auth_user_client.force_login(cls.auth_user)
        cls.data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug'
        }
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author,
        )

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создавать заметки."""
        url = reverse('notes:add')
        initial_count = Note.objects.count()
        response = self.client.post(url, self.data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), initial_count)

    def test_user_can_create_note(self):
        """Авторизованный пользователь может создавать заметки."""
        url = reverse('notes:add')
        initial_count = Note.objects.count()
        response = self.author_client.post(url, data=self.data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), initial_count + 1)
        new_note = Note.objects.order_by('-id').first()
        self.assertEqual(new_note.title, self.data['title'])
        self.assertEqual(new_note.text, self.data['text'])
        self.assertEqual(new_note.slug, self.data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_not_same_slug(self):
        """Невозможно создать две заметки с одинаковым slug."""
        url = reverse('notes:add')
        self.data['slug'] = self.note.slug
        response = self.author_client.post(url, data=self.data)
        self.assertFormError(response.context['form'], 'slug',
                             errors=(self.note.slug + WARNING))
        assert Note.objects.count() == 1

    def test_empty_lug(self):
        """
        Если при создании заметки не заполнен slug,
        то он формируется автоматически.
        """
        url = reverse('notes:add')
        data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
        }
        response = self.author_client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Note.objects.count(), 2)
        new_note = Note.objects.order_by('-id').first()
        expected_slug = slugify(data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_delete_note(self):
        """Пользователь может удалять свои заметки."""
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.author_client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        assert Note.objects.count() == 0

    def test_user_cant_delete_note_of_another_user(self):
        """Зарегестрированный пользователь не может удалять чужие заметки."""
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.auth_user_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)

    def test_author_can_edit_note(self):
        """Пользователь может редактировать свои заметки."""
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.author_client.post(url, self.data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        assert self.note.title == self.data['title']
        assert self.note.text == self.data['text']
        assert self.note.slug == self.data['slug']

    def test_author_cant_edit_note(self):
        """
        Зарегестрированный пользователь не может редактировать
        чужие заметки.
        """
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.auth_user_client.post(url, self.data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.note.id)
        assert self.note.title == note_from_db.title
        assert self.note.text == note_from_db.text
        assert self.note.slug == note_from_db.slug
