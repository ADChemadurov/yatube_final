from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        verbose_name="Название сообщества",
        help_text="Дайте подходящее название своему сообществу.",
        max_length=200,
    )
    slug = models.SlugField(
        verbose_name="Адрес страницы",
        unique=True,
        help_text="Укажите адрес для страницы задачи. Используйте только "
                  "латиницу, цифры, дефисы и знаки подчёркивания. "
                  "Если вы не укажете адрес, "
                  "то он будет автоматически сгенерирован.",
    )
    description = models.TextField(
        verbose_name="Описание сообщества",
        help_text="Опишите свое сообщество максимально подробно. "
                  "Или не описывайте. Это не обязательно.",
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name="Текст поста",
        help_text="Поделитесь своими мыслями или идеями.",
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации",
        auto_now_add=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор",
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name="posts",
        blank=True,
        null=True,
        verbose_name="Сообщество",
        help_text="Выберите сообщество для публикации поста. "
                  "А если хотите, то не выбирайте. Это необязательно.",
    )
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    class Meta():
        ordering = ("-pub_date",)

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    text = models.TextField(
        verbose_name="Текст комментария.",
        help_text="Поведайте, что вы думаете по поводу этого поста."
    )
    created = models.DateTimeField(
        verbose_name="Дата публикации комментария.",
        auto_now_add=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор комментария.",
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Пост к комментарию."
    )

    class Meta():
        ordering = ("-created",)


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор",
    )
