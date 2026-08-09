from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='test_user',
                                            password='password')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.user,
            slug='test-slug'
        )
        cls.other_user = User.objects.create(username='Другой юзер')

    def test_pages_availability(self):
        """Доступ страниц для аутентифицированного пользователя."""
        self.client.login(username='test_user', password='password')
        urls = (
            ('notes:home', None),
            ('notes:list', None),
            ('notes:success', None),
            ('notes:add', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_comment_edit_and_delete(self):
        """
        Страницы отдельной заметки, удаления и редактирования заметки
        доступны только автору заметки. Если на эти страницы попытается зайти
        другой пользователь — вернётся ошибка 404.
        """
        users_statuses = (
            (self.user, HTTPStatus.OK),
            (self.other_user, 404),
        )
        for current_user, expected_status in users_statuses:
            self.client.force_login(current_user)
            for name in ('notes:edit', 'notes:delete'):
                with self.subTest(user=current_user.username, action=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, expected_status)

    def test_redirect_for_anonymous_client(self):
        """
        При попытке перейти на страницу списка заметок,
        страницу успешного добавления записи,
        страницу добавления заметки, отдельной заметки,
        редактирования или удаления заметки анонимный пользователь
        перенаправляется на страницу логина.
        """
        login_url = reverse('users:login')
        no_arg_urls = ['notes:list', 'notes:add']
        for name in no_arg_urls:
            with self.subTest(name=name):
                url = reverse(name)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
        for name in ('notes:edit', 'notes:delete', 'notes:detail'):
            with self.subTest(name=name):
                url = reverse(name, args=(self.note.slug,))
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_pages_can(self):
        """
        Страницы регистрации пользователей,
        входа в учётную запись и выхода из неё доступны всем пользователям.
        """
        auth_names = ['notes:home', 'users:login', 'users:logout',
                      'users:signup']
        for name in auth_names:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                if name == 'users:logout':
                    allowed_statuses = {HTTPStatus.FOUND,
                                        HTTPStatus.METHOD_NOT_ALLOWED}
                    self.assertIn(
                        response.status_code,
                        allowed_statuses,
                    )
                else:
                    self.assertEqual(
                        response.status_code,
                        HTTPStatus.OK,
                    )
