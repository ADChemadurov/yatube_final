import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.core.cache import cache
from django.conf import settings
from django.urls import reverse
from django import forms

import datetime as dt

from posts.models import Post, Group, User


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создание тестового пользователя-автора.
        cls.user = User.objects.create_user(
            username="test-author",
            first_name="Test",
            last_name="Author",
        )
        # Создание тестовой группы.
        cls.group = Group.objects.create(
            id=1,
            title="Test Group",
            slug="test-slug",
            description="Test Description.",
        )
        # Создание тестового изображения.
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        # Создание 15 тестовых постов.
        for post_id in range(1, 16):
            Post.objects.create(
                id=post_id,
                author=User.objects.get(username="test-author"),
                text=f"Это тестовый текст поста {post_id}."*10,
                group=PostPagesTests.group,
                image=PostPagesTests.uploaded,
            )
        cls.post = Post.objects.get(id=15)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Чистим кэш перед каждым тестом, т.к. главная страница кэшируется.
        cache.clear()
        # Неавторизованный клиент.
        self.guest_client = Client()
        # Авторизованный клиент.
        self.user = User.objects.create_user(username="test-reader")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_correct_templates_used(self):
        """Тест на правильный шаблон."""
        templates_names = {
            reverse("index"): "index.html",
            reverse("group_url", kwargs={"slug": "test-slug"}): "group.html",
            reverse(
                "profile", kwargs={"username": "test-author"}
                ): "posts/profile.html",
            reverse(
                "post", kwargs={"username": "test-author", "post_id": "15"}
                ): "posts/post.html",
            reverse("new_post"): "posts/new_post.html",
        }
        for reverse_name, template in templates_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_edit_uses_correct_template(self):
        """
        Тест на использование правильного шаблона
        на странице редактирования поста.
        """
        self.authorized_client.force_login(PostPagesTests.user)
        response = self.authorized_client.get(reverse(
            "post_edit",
            kwargs={"username": "post_author", "post_id": "15"}
        ))
        self.assertTemplateUsed(response, "posts/new_post.html")

    def test_post_is_posted_on_main_page(self):
        """Проверяет, что текст поста появляется на главной странице."""
        response = self.guest_client.get(reverse("index"))
        text_in_response = response.context.get("page")[0].text
        text_expected = "Это тестовый текст поста 15."*10
        self.assertEqual(text_in_response, text_expected)

    def test_post_is_posted_on_group_page(self):
        """Проверяет, что текст поста появляется на странице группы."""
        response = self.guest_client.get(
            reverse("group_url", kwargs={"slug": "test-slug"})
        )
        text_in_response = response.context.get("page")[0].text
        text_expected = PostPagesTests.post.text
        self.assertEqual(text_in_response, text_expected)

    def test_post_is_not_posted_in_wrong_group(self):
        """
        Проверяет, что текст поста не появлется
        в непредназначенной для этого группе.
        """
        Group.objects.create(
            id=2,
            title="Wrong Group",
            slug="wrong-group",
            description="Test Description of a wrong group.",
        )
        post_in_wrong_group = Post.objects.create(
            text="Текст в неправильной группе.",
            author=User.objects.get(username="test-author"),
            group=Group.objects.get(id=2)
        )
        post_not_in_wrong_group = Post.objects.get(id=15)
        response = self.guest_client.get(
            reverse("group_url", kwargs={"slug": "wrong-group"})
        )
        posts_in_response = response.context.get("page").object_list
        # Группа доступна
        self.assertEqual(response.status_code, 200)
        # Проверка, что на странице постится пост предназначеный для нее.
        self.assertIn(post_in_wrong_group, posts_in_response)
        # Проверка, что на странице не постится пост другой группы.
        self.assertNotIn(post_not_in_wrong_group, posts_in_response)

    def test_author_page_has_author_post(self):
        """Проверка наличия поста на странице автора."""
        response = self.guest_client.get(reverse(
            "profile", kwargs={"username": "test-author"}
        ))
        text_in_response = response.context.get("page")[0].text
        text_expected = "Это тестовый текст поста 15."*10
        self.assertEqual(text_in_response, text_expected)

    def test_another_author_page_has_not_author_post(self):
        """
        Проверка отсуствия поста на странице автора,
        который не писал пост.
        """
        another_author = User.objects.create_user(
            username="wrong-author"
        )
        post_expected = Post.objects.create(
            author=another_author,
            text="Текст поста автора wrong-author."
        )
        post_not_expected = Post.objects.get(id=15)
        response = self.guest_client.get(reverse(
            "profile", kwargs={"username": "wrong-author"}
        ))
        text_in_response = response.context.get("page").object_list
        # Текст другого автора доступен на его странице.
        self.assertIn(post_expected, text_in_response)
        # Проверяем, что на его странице нет поста другого автора.
        self.assertNotEqual(post_not_expected, text_in_response)

    def test_post_is_on_post_page(self):
        """Проверка наличия поста на отдельной странице."""
        response = self.guest_client.get(reverse(
            "post", kwargs={"username": "test-author", "post_id": "15"}
        ))
        text_in_response = response.context.get("post").text
        text_expected = "Это тестовый текст поста 15."*10
        self.assertEqual(text_in_response, text_expected)

    def test_post_is_not_available_at_wrong_post_page(self):
        """Проверка отсутствия поста на странице другого поста."""
        response = self.guest_client.get(reverse(
            "post", kwargs={"username": "test-author", "post_id": "14"}
        ))
        text_in_response = response.context.get("post")
        text_not_expected = "Это тестовый текст поста 15."*10
        self.assertNotEqual(text_not_expected, text_in_response)

    def test_post_edit_changes_correct_post_text(self):
        """Проверка что редактироваться будет верный текст поста."""
        self.authorized_client.force_login(
            User.objects.get(username="test-author")
        )
        response = self.authorized_client.get(reverse(
            "post_edit",
            kwargs={"username": "test-author", "post_id": "15"}
        ))
        text_in_form = str(response.context.get("form").instance)
        text_expected = "Это тестовый текст поста 15."[:15]
        self.assertEqual(text_expected, text_in_form)

    # Тесты проверки контекста.
    def test_homepage_gets_correct_context(self):
        """Проверяет контекст на главной странице."""
        response = self.guest_client.get(reverse("index"))
        post_text_0 = response.context.get("page")[0].text
        post_author_0 = response.context.get("page")[0].author
        post_group_0 = response.context.get("page")[0].group
        post_pub_date_0 = response.context.get("page")[0].pub_date
        author_expected = User.objects.get(username="test-author")
        post_image_0 = response.context.get("page")[0].image
        image_expected = Post.objects.get(id=15).image
        self.assertEqual(post_text_0, "Это тестовый текст поста 15."*10)
        self.assertEqual(post_author_0, author_expected)
        self.assertEqual(post_group_0, PostPagesTests.group)
        self.assertEqual(
            post_pub_date_0.strftime("%d/%m/%Y"),
            dt.date.today().strftime("%d/%m/%Y")
        )
        self.assertEqual(post_image_0, image_expected)

    def test_group_page_gets_correct_context(self):
        """Проверяет контест передаваемый на страницу группы."""
        response = self.guest_client.get(
            reverse("group_url", kwargs={"slug": "test-slug"})
        )
        post_text_0 = response.context.get("page")[0].text
        post_author_0 = response.context.get("page")[0].author
        post_group_0 = response.context.get("page")[0].group
        post_pub_date_0 = response.context.get("page")[0].pub_date
        author_expected = User.objects.get(username="test-author")
        post_image_0 = response.context.get("page")[0].image
        image_expected = Post.objects.get(id=15).image
        self.assertEqual(post_text_0, "Это тестовый текст поста 15."*10)
        self.assertEqual(post_author_0, author_expected)
        self.assertEqual(post_group_0, PostPagesTests.group)
        self.assertEqual(
            post_pub_date_0.strftime("%d/%m/%Y"),
            dt.date.today().strftime("%d/%m/%Y")
        )
        self.assertEqual(post_image_0, image_expected)

    def test_new_post_page_gets_correct_context(self):
        """Проверяет контекст формы создания нового поста."""
        response = self.authorized_client.get(reverse("new_post"))
        form_fields = {
            "group": forms.models.ModelChoiceField,
            "text": forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_author_page_gets_correct_context(self):
        """Проверяет контест передаваемый на страницу автора."""
        response = self.guest_client.get(
            reverse("profile", kwargs={"username": "test-author"})
        )
        post_text_0 = response.context.get("page")[0].text
        post_author_0 = response.context.get("page")[0].author
        post_group_0 = response.context.get("page")[0].group
        post_pub_date_0 = response.context.get("page")[0].pub_date
        author_username = post_author_0.username
        posts_qty_expected = response.context.get("posts_number")
        username_expected = User.objects.get(username="test-author")
        fullname_expected = User.objects.get(
            username="test-author").get_full_name()
        post_image_0 = response.context.get("page")[0].image
        image_expected = Post.objects.get(id=15).image
        self.assertEqual(post_text_0, "Это тестовый текст поста 15."*10)
        self.assertEqual(post_author_0, username_expected)
        self.assertEqual(post_group_0, PostPagesTests.group)
        self.assertEqual(
            post_pub_date_0.strftime("%d/%m/%Y"),
            dt.date.today().strftime("%d/%m/%Y")
        )
        self.assertEqual(author_username, "test-author")
        self.assertEqual(fullname_expected, "Test Author")
        self.assertEqual(posts_qty_expected, 15)
        self.assertEqual(post_image_0, image_expected)

    def test_post_page_gets_correct_context(self):
        """Проверяет контест передаваемый на страницу поста."""
        response = self.guest_client.get(reverse(
            "post",
            kwargs={"username": "test-author", "post_id": "15"})
        )
        post_text_0 = response.context.get("post").text
        post_author_0 = response.context.get("post").author
        post_group_0 = response.context.get("post").group
        post_pub_date_0 = response.context.get("post").pub_date
        author_username = post_author_0.username
        posts_qty_expected = response.context.get("posts_number")
        username_expected = User.objects.get(username="test-author")
        fullname_expected = User.objects.get(
            username="test-author").get_full_name()
        post_image_0 = response.context.get("post").image
        image_expected = Post.objects.get(id=15).image
        self.assertEqual(post_text_0, "Это тестовый текст поста 15."*10)
        self.assertEqual(post_author_0, username_expected)
        self.assertEqual(post_group_0, PostPagesTests.group)
        self.assertEqual(
            post_pub_date_0.strftime("%d/%m/%Y"),
            dt.date.today().strftime("%d/%m/%Y")
        )
        self.assertEqual(author_username, "test-author")
        self.assertEqual(fullname_expected, "Test Author")
        self.assertEqual(posts_qty_expected, 15)
        self.assertEqual(post_image_0, image_expected)

    def test_post_edit_page_gets_correct_context(self):
        """Проверяет контекст передаваемый в форму редактирования поста."""
        self.authorized_client.force_login(
            User.objects.get(username="test-author")
        )
        response = self.authorized_client.get(reverse(
            "post_edit",
            kwargs={"username": "test-author", "post_id": "15"}
        ))
        form_fields = {
            "group": forms.models.ModelChoiceField,
            "text": forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context.get("is_edit"), True)
        self.assertEqual(response.context.get("username"), "test-author")
        self.assertEqual(response.context.get("post_id"), 15)

    # Тесты паджинатора.
    def test_1st_homepage_has_10_records(self):
        """На 1-ой странице главной страницы находится 10 постов."""
        response = self.client.get(reverse("index"))
        self.assertEqual(len(response.context.get("page").object_list), 10)

    def test_2nd_page_has_5_records(self):
        """На 2-ой странице главной страницы находится 5 постов."""
        response = self.client.get(reverse("index") + "?page=2")
        self.assertEqual(len(response.context.get("page").object_list), 5)

    def test_1st_group_page_has_10_records(self):
        """На 1-ой странице группы находится 10 постов из 15."""
        response = self.client.get(
            reverse("group_url", kwargs={"slug": "test-slug"})
        )
        self.assertEqual(len(response.context.get("page").object_list), 10)

    def test_2nd_group_page_has_5_records(self):
        """На 2-ой странице группы находится 5 постов из 15."""
        response = self.client.get(
            reverse("group_url", kwargs={"slug": "test-slug"}) + "?page=2"
        )
        self.assertEqual(len(response.context.get("page").object_list), 5)
