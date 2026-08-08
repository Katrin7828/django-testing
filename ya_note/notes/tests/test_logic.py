from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

from pytils.translit import slugify

User = get_user_model()


class TestNoteCreation(TestCase):
    NOTE_TEXT = 'Текст'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='user')
        cls.notes = Note.objects.create(title='Заголовок', text='Текст',
                                        author=cls.user,
                                        slug='test-slug')
        cls.url = reverse('notes:detail', args=(cls.notes.id,))
        cls.create_url = reverse('notes:add')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {'text': cls.NOTE_TEXT}
        cls.author = User.objects.create(username='author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создавать заметки."""
        notes_count_before = Note.objects.count()
        self.client.post(self.url, data=self.form_data)
        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before)

    def test_user_can_create_note(self):
        """Авторизоанный пользователь может создавать заметки."""
        response = self.auth_client.post(self.create_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.author, self.user)

    def test_not_same_slug(self):
        """Невозможно создать две заметки с одинаковым slug."""
        duplicate_slug = self.notes.title
        data_with_duplicate_slug = {
            'title': duplicate_slug,
            'text': 'Текст новой заметки',
        }
        response = self.auth_client.post(self.create_url,
                                         data=data_with_duplicate_slug)
        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Note.objects.count(), 2)
        new_note = Note.objects.order_by('-id').first()
        self.assertNotEqual(new_note.slug, self.notes.slug)
        self.assertTrue(new_note.slug)

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
        """Автор может удалять свои заметки."""
        count_before = Note.objects.count()
        url = reverse('notes:delete', args=(self.notes.slug,))
        response = self.auth_client.delete(url)
        count_after = Note.objects.count()
        self.assertEqual(count_after, count_before - 1)
        self.assertRedirects(response, reverse('notes:success'))

    def test_user_cant_delete_note_of_another_user(self):
        """Автор не может удалять чужие заметки."""
        response = self.auth_client.delete(self.notes.slug,)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        """Автор может редактировать свои заметки."""
        url = reverse('notes:edit', args=(self.notes.slug,))
        new_title = 'Отредактированный заголовок'
        new_text = 'Отредактированный текст заметки'
        form_data = {
            'title': new_title,
            'text': new_text
        }
        response = self.auth_client.post(url, data=form_data)
        self.assertIn(response.status_code, [200, 302, 303])
        self.notes.refresh_from_db()
        self.assertEqual(self.notes.title, new_title)
        self.assertEqual(self.notes.text, new_text)

    def test_author_cant_edit_note(self):
        """Автор не может редактировать чужие заметки."""
        url = reverse('notes:edit', args=(self.notes.slug,))
        new_title = 'Отредактированный заголовок'
        new_text = 'Отредактированный текст заметки'
        form_data = {
            'title': new_title,
            'text': new_text,
        }
        response = self.author_client.post(url, data=form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.notes.refresh_from_db()
        self.assertEqual(self.notes.title, 'Заголовок')
        self.assertEqual(self.notes.text, 'Текст')
