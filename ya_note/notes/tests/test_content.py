from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note

User = get_user_model()


class TestNotesListLogic(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(username='author',
                                              password='pass')
        cls.other_user = User.objects.create_user(username='other_user',
                                                  password='pass')
        cls.note = Note.objects.create(
            title='Заметка первого',
            text='Текст заметки',
            author=cls.author,
        )
        cls.list_url = reverse('notes:list')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.other_user_client = Client()
        cls.other_user_client.force_login(cls.other_user)

    def setUp(self):
        self.client.login(username='author', password='pass')

    def test_object_list(self):
        """
        Отдельная заметка передаётся на страницу со списком заметок.
        В список заметок одного пользователя не попадают заметки другого.
        """
        user_status = (
            (self.author_client, True),
            (self.other_user_client, False),
        )
        for client, note_in_list in user_status:
            with self.subTest():
                response = client.get(self.list_url)
                self.assertIn('object_list', response.context)
                object_list = response.context['object_list']
                self.assertIs((self.note in object_list), note_in_list)

    def test_add_and_edit_page(self):
        """На страницы создания и редактирования заметки передаются формы."""
        url = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        for name, args in url:
            with self.subTest():
                url = reverse(name, args=args)
                response = self.author_client.get(url)
                self.assertIn('form', response.context)
