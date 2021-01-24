from django.test import TestCase, Client

from posts.models import Post, Group, User


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
        }
        for url, response_code in requests.items():
            with self.subTest(response_code=response_code):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, response_code)

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
