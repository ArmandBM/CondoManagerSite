from django.contrib.auth import get_user_model
from django.db.models import BigAutoField
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .models import Apartment, Complains, Package, User


class PrimaryKeyTests(SimpleTestCase):
    def test_primary_keys_match_initial_migration(self):
        for model in (Apartment, Complains, Package, User):
            with self.subTest(model=model.__name__):
                self.assertIsInstance(model._meta.pk, BigAutoField)


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
