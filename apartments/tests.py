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


class ComplainsViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="resident")
        self.client.force_login(self.user)
        self.url = reverse("complains")

    def test_refresh_after_submission_does_not_duplicate_complaint(self):
        complaint = "The hallway light is out."
        response = self.client.post(self.url, {"complain": complaint}, follow=True)

        self.assertRedirects(response, self.url)
        self.assertContains(response, complaint)
        self.assertContains(self.client.get(self.url), complaint)
        self.assertEqual(Complains.objects.count(), 1)
        self.assertEqual(Complains.objects.get().user, self.user)

    def test_empty_complaint_renders_error_without_creating_record(self):
        response = self.client.post(self.url, {"complain": ""})

        self.assertTemplateUsed(response, "apartments/complain.html")
        self.assertContains(response, "Please enter a complaint before submitting.")
        self.assertEqual(Complains.objects.count(), 0)
