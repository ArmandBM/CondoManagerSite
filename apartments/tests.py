import re

from django.contrib.auth import SESSION_KEY, get_user_model
from django.test import Client, TestCase
from django.urls import reverse


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


class LogoutViewTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user = get_user_model().objects.create_user(username="resident")
        self.client.force_login(self.user)
        self.logout_url = reverse("logout")

    def test_get_is_rejected_and_preserves_session(self):
        response = self.client.get(self.logout_url)

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "POST")
        self.assertEqual(self.client.session[SESSION_KEY], str(self.user.pk))

    def test_post_without_token_is_rejected_and_preserves_session(self):
        self.client.get(reverse("index"))

        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.session[SESSION_KEY], str(self.user.pk))

    def test_post_with_form_token_ends_session_and_redirects_to_login(self):
        response = self.client.get(reverse("index"))
        form = re.search(
            rf'<form action="{re.escape(self.logout_url)}" method="post">(.*?)</form>',
            response.content.decode(),
            re.DOTALL,
        )
        self.assertIsNotNone(form)
        token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', form[1])
        self.assertIsNotNone(token)

        response = self.client.post(self.logout_url, {"csrfmiddlewaretoken": token[1]})

        self.assertRedirects(response, reverse("login"))
        self.assertNotIn(SESSION_KEY, self.client.session)
