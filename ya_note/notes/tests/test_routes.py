from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='test_user')
        cls.other_user = User.objects.create_user(username='other_user')
        cls.other_client = Client()
        cls.other_client.force_login(cls.other_user)
        cls.author = User.objects.create_user(username='author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author,
            slug='test-slug'
        )
        cls.home_url = reverse('notes:home')
        cls.list_url = reverse('notes:list')
        cls.success_url = reverse('notes:success')
        cls.add_url = reverse('notes:add')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.detail_url = reverse('notes:detail', args=(cls.note.slug,))
        cls.logout_url = reverse('users:logout')
        cls.login_url = reverse('users:login')
        cls.signup_url = reverse('users:signup')

    def test_pages_availability(self):
        """Доступ страниц для аутентифицированного пользователя."""
        # Я объединила первые два теста из ТЗ по этому файлу,
        # оттуда и home появился
        urls = [
            self.home_url,
            self.list_url,
            self.success_url,
            self.add_url,
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_comment_edit_and_delete(self):
        """
        Страницы отдельной заметки, удаления и редактирования заметки
        доступны только автору заметки. Если на эти страницы попытается зайти
        другой пользователь — вернётся ошибка 404.
        """
        client_statuses = (
            (self.author_client, HTTPStatus.OK),
            (self.other_client, HTTPStatus.NOT_FOUND),
        )
        urls = (
            self.edit_url,
            self.delete_url,
        )
        for client, expected_status in client_statuses:
            for url in urls:
                with self.subTest(client=client, url=url):
                    response = client.get(url)
                    self.assertEqual(response.status_code, expected_status)

    def test_redirect_for_anonymous_client(self):
        """
        При попытке перейти на страницу списка заметок,
        страницу успешного добавления записи,
        страницу добавления заметки, отдельной заметки,
        редактирования или удаления заметки анонимный пользователь
        перенаправляется на страницу логина.
        """
        urls = (
            self.add_url,
            self.list_url,
            self.edit_url,
            self.delete_url,
            self.detail_url,
        )
        for url in urls:
            with self.subTest(url=url):
                redirect_url = f'{self.login_url}?next={url}'
                # тут, получается, не получится вынести это,
                # тк перебираем url из списка
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_pages_can(self):
        """
        Страницы регистрации пользователей,
        входа в учётную запись доступны всем пользователям.
        """
        urls = (
            self.home_url,
            self.login_url,
            self.signup_url,
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_logout_can(self):
        """Страница выхода из учетной записи доступна всем пользователям."""
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
