import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from posts.forms import PostForm
from posts.models import Post, Group, User


class NewPostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Создание тестовой группы.
        Group.objects.create(
            id=1,
            title="Test Group",
            slug="test-slug",
            description="Test Description.",
        )
        cls.group = Group.objects.get(id=1)

        # Создание тестового поста.
        Post.objects.create(
            id=1,
            author=User.objects.create_user(
                "test-author",
                "testname@testhost.test",
                "testsneverfail"),
            text="Это тестовый текст."*10,
            group=NewPostFormTests.group,
        )
        cls.post = Post.objects.get(id=1)

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

        # Создание тестовой формы.
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Неавторизованный клиент.
        self.guest_client = Client()
        # Авторизованный клиент.
        self.user = User.objects.get(username="test-author")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_correct_labels_assigned(self):
        """Проверяет, что в форму переданы правильные labels."""
        form_labels = {
            "group": "Сообщество:",
            "text": "Текст поста:",
        }
        for value, expected in form_labels.items():
            with self.subTest(value=value):
                form_label = NewPostFormTests.form.fields[value].label
                self.assertEqual(form_label, expected)

    def test_correct_help_texts_assigned(self):
        """Проверяет, что в форму переданы правильные help_texts."""
        form_help_texts = {
            "group": "Вы можете выбрать сообщество, "
                     "в котором будет опубликован Ваш пост. "
                     "Необязательно к заполненинию.",
            "text": "Поделитесь своими мыслями, новостями или событиями.",
        }
        for value, expected in form_help_texts.items():
            with self.subTest(value=value):
                form_help_text = NewPostFormTests.form.fields[value].help_text
                self.assertEqual(form_help_text, expected)

    def test_new_post_created(self):
        """
        Проверяет, что создается новый пост, сохраняется в базе данных,
        а пользователя переводит на главную страницу.
        """
        posts_count = Post.objects.count()
        form_data = {
            "text": "Текст нового тестового поста",
            "image": NewPostFormTests.uploaded,
        }
        response = self.authorized_client.post(
            reverse("new_post"),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse("index"))
        self.assertEqual(Post.objects.count(), posts_count+1)
        self.assertTrue(Post.objects.filter(id=2).exists())

    def test_post_edit_changes_post_text(self):
        """Проверяет, что текст поста был изменен и сохранен в базе."""
        posts_count = Post.objects.count()
        form_data = {
            "text": "Измененый текст поста",
        }
        response = self.authorized_client.post(reverse(
            "post_edit",
            kwargs={"username": "test-author", "post_id": "1"}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            "post", kwargs={"username": "test-author", "post_id": "1"}
        ))
        # Проверка на то, что постов не стало больше.
        self.assertEqual(Post.objects.count(), posts_count)
        # Проверка на то, что текст поста изменился.
        self.assertEqual(Post.objects.get(id=1).text, "Измененый текст поста")

    # Не изменяется группа, выдает ошибку.
    def test_post_edit_changes_post_group(self):
        """Проверяет, что группа поста была изменена и сохранена в базе."""
        Group.objects.create(
            id=2,
            title="New Test Group",
            slug="new-test-group",
        )
        posts_count = Post.objects.count()
        form_data = {
            "text": "Измененный текст новой записи",
            "group": Group.objects.get(id=2).id,
        }
        response = self.authorized_client.post(reverse(
            "post_edit",
            kwargs={"username": "test-author", "post_id": "1"}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            "post", kwargs={"username": "test-author", "post_id": "1"}
        ))
        # Проверка на то, что постов не стало больше.
        self.assertEqual(Post.objects.count(), posts_count)
        # Проверка на то, что группа поста изменилась.
        self.assertEqual(
            Post.objects.get(id=1).group,
            Group.objects.get(id=2)
            )
