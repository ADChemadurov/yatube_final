from django.test import TestCase, TransactionTestCase

from posts.models import Comment, Follow, Post, Group, User


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


class CommentModelTest(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            id=1,
            author=User.objects.create_user("test-author"),
            text="Это тестовый текст."*10,
        )

        cls.comment = Comment.objects.create(
            id=1,
            post=Post.objects.get(id=cls.post.id),
            text="Тест тестового коммента.",
            author=User.objects.create_user("test-commenter"),
        )

    def test_verbose_names(self):
        comment = CommentModelTest.comment
        field_verboses = {
            "text": "Текст комментария.",
            "created": "Дата публикации комментария.",
            "author": "Автор комментария.",
            "post": "Пост к комментарию.",
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    comment._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        comment = CommentModelTest.comment
        field_help_text = {
            "text": "Поведайте, что вы думаете по поводу этого поста.",
        }
        for value, expected in field_help_text.items():
            with self.subTest(value=value):
                self.assertEqual(
                    comment._meta.get_field(value).help_text, expected)

    def test_object_value_is_text_field(self):
        comment = CommentModelTest.comment
        expected_object_value = "Тест тестового коммента."[:15]
        self.assertEqual(expected_object_value, str(comment))


class FollowModelTest(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower = User.objects.create(username="test-follower")
        cls.followed = User.objects.create(username="test-followed")
        cls.follow = Follow.objects.create(
            user=FollowModelTest.follower,
            author=FollowModelTest.followed,
        )

    def test_verbose_names(self):
        follow = FollowModelTest.follow
        field_verboses = {
            "user": "Подписчик",
            "author": "Автор",
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    follow._meta.get_field(value).verbose_name, expected)
