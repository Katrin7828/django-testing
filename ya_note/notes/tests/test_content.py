from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from http import HTTPStatus

from notes.models import Note

User = get_user_model()


class TestNotesListLogic(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_first = User.objects.create_user(username='test_user',
                                                  password='password')
        cls.user_second = User.objects.create_user(username='second',
                                                   password='password')
        cls.note_first = Note.objects.create(
            title='Заметка первого',
            text='Текст заметки',
            author=cls.user_first
        )
        cls.note_second = Note.objects.create(
            title='Заметка второго',
            text='Текст заметки',
            author=cls.user_second
        )

    def test_note_is_in_object_list(self):
        """Отдельная заметка передаётся на страницу со списком заметок."""
        self.client.login(username='test_user', password='password')
        url = reverse('notes:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('object_list', response.context)
        object_list = response.context['object_list']
        found_note = None
        for note_in_list in object_list:
            if note_in_list.pk == self.note_first.pk:
                found_note = note_in_list
                break
        self.assertIsNotNone(found_note)

    def test_object_list(self):
        """В список заметок одного пользователя не попадают заметки другого."""
        self.client.login(username='test_user', password='password')
        response = self.client.get(reverse('notes:list'))
        my_notes = response.context['object_list']
        self.assertNotIn(self.note_second, my_notes)

    def test_add_and_edit(self):
        """На страницы создания и редактирования заметки передаются формы."""
        self.client.login(username='test_user', password='password')
        with self.subTest(page='create_note'):
            response = self.client.get(reverse('notes:add'))
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIn('form', response.context)
        with self.subTest(page='create_edit'):
            response = self.client.get(reverse('notes:edit',
                                               args=(self.note_first.slug,)))
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIn('form', response.context)
