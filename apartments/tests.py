from contextlib import redirect_stdout
from io import StringIO

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Apartment, Complains


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
    def test_resident_sees_complaint_without_exposing_data_on_stdout(self):
        apartment = Apartment.objects.create(name="TESTE-101")
        resident = get_user_model().objects.create_user(
            username="morador_sintetico",
            apartament=apartment,
        )
        complaint_text = "Reclamação sintética sobre o interfone."
        Complains.objects.create(user=resident, complain_text=complaint_text)
        self.client.force_login(resident)

        stdout = StringIO()
        with redirect_stdout(stdout):
            response = self.client.get(reverse("complains"))

        self.assertContains(response, complaint_text)
        for private_value in (complaint_text, apartment.name, resident.username):
            with self.subTest(private_value=private_value):
                self.assertNotIn(private_value, stdout.getvalue())
