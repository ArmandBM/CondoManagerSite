from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Complains


class LoginViewTests(TestCase):
    def setUp(self):
        self.password = "CorrectHorseBatteryStaple123!"
        self.user = get_user_model().objects.create_user(
            username="resident",
            password=self.password,
        )

    def test_valid_credentials_log_user_in(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.user.username, "password": self.password},
        )

        self.assertRedirects(
            response,
            reverse("index"),
            fetch_redirect_response=False,
        )
        self.assertEqual(
            self.client.session["_auth_user_id"],
            str(self.user.pk),
        )

    def test_invalid_password_shows_error(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.user.username, "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["error"],
            "Invalid username or password.",
        )


class ComplaintViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="resident")
        self.client.force_login(self.user)

    def test_rejects_whitespace_only_complaints(self):
        count = Complains.objects.count()
        for text in ("   ", "\r\n\n", " \t\n "):
            with self.subTest(text=text):
                response = self.client.post(reverse("complains"), {"complain": text})

                self.assertContains(response, "Please enter a complaint before submitting.")
                self.assertEqual(Complains.objects.count(), count)

    def test_preserves_formatting_of_valid_complaint(self):
        text = "  First line\n  Second line  "

        response = self.client.post(reverse("complains"), {"complain": text})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Complains.objects.get(user=self.user).complain_text, text)
