from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ("group", "text", "image")
        labels = {
            "group": _("Сообщество:"),
            "text": _("Текст поста:"),
        }
        help_texts = {
            "group": _(
                "Вы можете выбрать сообщество, "
                "в котором будет опубликован Ваш пост. "
                "Необязательно к заполненинию."
            ),
            "text": _("Поделитесь своими мыслями, новостями или событиями.")
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ("text", )
        labels = {"text": _("Текст комментария:")}
        help_texts = {
            "text": _("Поведайте, что вы думаете по поводу этого поста.")
        }
