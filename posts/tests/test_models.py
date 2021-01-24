from django.test import TestCase

from posts.models import Post, Group, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            id=1,
            author=User.objects.create_user(
                "Mr. Testname",
                "testname@testhost.test",
                "testsneverfail"),
            text="Это тестовый текст."*10,
        )

    def test_verbose_names(self):
        post = PostModelTest.post
        field_verboses = {
            "text": "Текст поста",
            "pub_date": "Дата публикации",
            "author": "Автор",
            "group": "Сообщество",
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        post = PostModelTest.post
        field_help_text = {
            "text": "Поделитесь своими мыслями или идеями.",
            "group": "Выберите сообщество для публикации поста. "
                     "А если хотите, то не выбирайте. Это необязательно.",
        }
        for value, expected in field_help_text.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_object_value_is_text_field(self):
        post = PostModelTest.post
        expected_object_value = ("Это тестовый текст."*10)[:15]
        self.assertEqual(expected_object_value, str(post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            id=1,
            title="Test Group",
            slug="test-slug",
            description="Test Description.",
        )

    def test_verbose_names(self):
        group = GroupModelTest.group
        field_verboses = {
            "title": "Название сообщества",
            "slug": "Адрес страницы",
            "description": "Описание сообщества",
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        group = GroupModelTest.group
        field_help_text = {
            "title": "Дайте подходящее название своему сообществу.",
            "slug": "Укажите адрес для страницы задачи. Используйте только "
                    "латиницу, цифры, дефисы и знаки подчёркивания. "
                    "Если вы не укажете адрес, "
                    "то он будет автоматически сгенерирован.",
            "description": "Опишите свое сообщество максимально подробно. "
                           "Или не описывайте. Это не обязательно.",
        }
        for value, expected in field_help_text.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).help_text, expected)

    def test_object_value_is_title_field(self):
        group = GroupModelTest.group
        expected_object_title = group.title
        self.assertEqual(expected_object_title, str(group))
