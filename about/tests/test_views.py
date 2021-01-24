from django.test import TestCase, Client
from django.urls import reverse


class StaticPagesTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_correct_templates_used(self):
        """Тест на правильный шаблон."""
        templates_names = {
            "author.html": reverse("about:author"),
            "tech.html": reverse("about:tech"),
        }
        for template, reverse_name in templates_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
