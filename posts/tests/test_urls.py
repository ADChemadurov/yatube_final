from django.test import TestCase, Client
from django.urls.base import reverse

from posts.models import Follow, Post, Group, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Cоздание тестового автора поста.
        cls.author = User.objects.create_user(username="test-author")
        # Создание тестовой группы.
        cls.group = Group.objects.create(
            id=1,
            title="Test Group",
            slug="test-slug",
            description="Test Description.",
        )

        # Создание тестового поста.
        Post.objects.create(
            id=1,
            author=PostsURLTests.author,
            text="Это тестовый текст."*10,
        )
        cls.post = Post.objects.get(id=1)

    def setUp(self):
        # Неавторизованный клиент.
        self.guest_client = Client()
        # Авторизованный клиент.
        self.user = User.objects.create_user(username="test-reader")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_error_404_page_available(self):
        """Проверяет, что ненайденная страница возвращает код 404."""
        response = self.guest_client.get("/nonexistent-page/")
        self.assertEqual(response.status_code, 404)

    def test_page_available_for_unauth_user(self):
        """
        Тест доступа к страницам для неавторизованого пользователя.
        Страница создания поста и его редактирования должны осуществлять
        перенаправление неавторизованого пользователя, т.е. код 302.
        """
        requests = {
            "/": 200,
            "/group/test-slug/": 200,
            "/new/": 302,
            "/test-author/": 200,
            "/test-author/1/": 200,
            "/test-author/1/edit/": 302,
            "/follow/": 302,
            "/test-author/follow/": 302,
            "/test-author/unfollow/": 302,
            "/test-author/1/comment/": 302,
        }
        for url, response_code in requests.items():
            with self.subTest(response_code=response_code):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, response_code)

    def test_page_available_for_auth_user(self):
        """
        Тест доступа к страницам под логином читателя (не автора постов).
        Страница редактирования поста должна перенаправить читателя,
        т.е. response code код 302.
        """
        requests = {
            "/": 200,
            "/group/test-slug/": 200,
            "/new/": 200,
            "/test-author/": 200,
            "/test-author/1/": 200,
            "/test-author/1/edit/": 302,
            "/test-author/follow/": 302,
            "/follow/": 200,
            "/test-author/unfollow/": 302,
            # add_comment, возвращает 404, а не 200!
            # "/test-author/1/comment/": 200,
        }
        for url, response_code in requests.items():
            with self.subTest(response_code=response_code):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, response_code)

    def test_add_comment_available(self):
        response_unauth = self.guest_client.get(reverse(
            "add_comment", kwargs={"username": "test-author", "post_id": "1"}
        ))
        self.assertEqual(response_unauth.status_code, 302)
        response_auth = self.authorized_client.get(reverse(
            "add_comment", kwargs={"username": "test-author", "post_id": "1"}
        ))
        self.assertEqual(response_auth.status_code, 200)

    def test_author_can_access_post_edit_page(self):
        """Тест доступа к странице редактирования поста его автором."""
        # Перелогиниваемся как автор поста.
        self.authorized_client.force_login(PostsURLTests.author)
        # Пытаемся получить доступ к странице редактирования поста.
        response = self.authorized_client.get("/test-author/1/edit/")
        self.assertEqual(response.status_code, 200)

    def test_new_post_redirect(self):
        """
        Тест перенаправления на авторизацию в случае если
        неавторизованный пользователь пытается попасть
        на страницу создания поста.
        """
        response = self.guest_client.get("/new/", follow=True)
        self.assertRedirects(
            response,
            "/auth/login/?next=/new/"
        )

    def test_post_edit_redirects_unauth_user(self):
        """
        Тест перенаправления на авторизацию в случае если
        неавторизованный пользователь пытается попасть
        на страницу редактирования поста.
        """
        response = self.guest_client.get("/test-author/1/edit/", follow=True)
        self.assertRedirects(
            response,
            "/auth/login/?next=/test-author/1/edit/"
        )

    def test_post_edit_redirects_non_author(self):
        """
        Тест перенаправления на авторизацию в случае если
        авторизованный пользователь, но не автор поста пытается попасть
        на страницу редактирования поста.
        """
        response = self.authorized_client.get(
            "/test-author/1/edit/", follow=True
        )
        self.assertRedirects(
            response,
            "/test-author/1/"
        )

    def test_follow_sucessful_redirect(self):
        """ Тест на работу перенаправления при подписке """
        # Тест на редирект при успешной подписке.
        response_1 = self.authorized_client.get(
            "/test-author/follow/", follow=True
        )
        follows_qty_1 = Follow.objects.all().count()
        self.assertRedirects(response_1, "/test-author/")
        self.assertEqual(follows_qty_1, 1)

        # Тест на редирект при уже существующей подписке.
        # Нельзя подписаться дважды.
        response_2 = self.authorized_client.get(
            "/test-author/follow/", follow=True
        )
        follows_qty_2 = Follow.objects.all().count()
        self.assertRedirects(response_2, "/test-author/")
        self.assertEqual(follows_qty_2, 1)

        # Тест на редирект при успешной отписке.
        response_3 = self.authorized_client.get(
            "/test-author/unfollow/", follow=True
        )
        follows_qty_3 = Follow.objects.all().count()
        self.assertRedirects(response_3, "/test-author/")
        self.assertEqual(follows_qty_3, 0)

        # Тест на редирект при отсутствующей подписке.
        # Нельзя отписать дважды или если не было подписки.
        response_4 = self.authorized_client.get(
            "/test-author/unfollow/", follow=True
        )
        follows_qty_4 = Follow.objects.all().count()
        self.assertRedirects(response_4, "/test-author/")
        self.assertEqual(follows_qty_4, 0)

        # Тест на редирект при подписке на самого себя.
        self.authorized_client.force_login(PostsURLTests.author)
        response_5 = self.authorized_client.get(
            "/test-author/follow/", follow=True
        )
        follows_qty_5 = Follow.objects.all().count()
        self.assertRedirects(response_5, "/test-author/")
        self.assertEqual(follows_qty_5, 0)

    def test_add_comment_redirects(self):
        """
        Тест на редирект при создании комментария
        неавторизованным пользователем.
        """
        response = self.guest_client.get(reverse(
            "add_comment", kwargs={"username": "test-author", "post_id": "1"}
        ))
        self.assertRedirects(
            response, "/auth/login/?next=/test-author/1/comment/"
        )

    def test_correct_templates_used(self):
        """Тест на правильность использования шаблонов."""
        templates_url_names = {
            "index.html": "/",
            "group.html": "/group/test-slug/",
            "posts/new_post.html": "/new/",
        }
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
