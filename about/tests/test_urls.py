from django.test import TestCase, Client


class StaticPagesTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_author_page(self):
        """Тест доступа к станице 'Об авторе'."""
        response = self.guest_client.get("/about/author/")
        self.assertEqual(response.status_code, 200)

    def test_technologies_page(self):
        """Тест доступа к станице 'Технологии'."""
        response = self.guest_client.get("/about/tech/")
        self.assertEqual(response.status_code, 200)

    def test_correct_templates_used(self):
        """Тест на правильность использования шаблонов."""
        templates_url_names = {
            "author.html": "/about/author/",
            "tech.html": "/about/tech/",
        }
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
