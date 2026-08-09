from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestNotesListLogic(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(username='author',
                                              password='pass')
        cls.other_user = User.objects.create_user(username='other',
                                                  password='pass')
        cls.note_first = Note.objects.create(
            title='Заметка первого',
            text='Текст заметки',
            author=cls.author,
        )

    def setUp(self):
        self.client.login(username='author', password='pass')

    def test_note_is_in_object_list(self):
        """Отдельная заметка передаётся на страницу со списком заметок."""
        url = reverse('notes:list')
        response = self.client.get(url)
        object_list = response.context['object_list']
        self.assertIn(self.note_first, object_list)

    def test_object_list(self):
        """В список заметок одного пользователя не попадают заметки другого."""
        self.client.login(username='other', password='pass')
        url = reverse('notes:list')
        response = self.client.get(url)
        object_list = response.context['object_list']
        self.assertNotIn(self.note_first, object_list)

    def test_add_page(self):
        """На страницы создания заметки передаются формы."""
        url = reverse('notes:add')
        response = self.client.get(url)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], NoteForm)

    def test_edit_page(self):
        """На страницы редактирования заметки передаются формы."""
        url = reverse('notes:edit', args=[self.note_first.slug])
        response = self.client.get(url)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], NoteForm)
