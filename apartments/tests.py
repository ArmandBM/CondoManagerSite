from contextlib import redirect_stdout
from io import StringIO

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Apartment, Complains, Package


class ResidentListingPrivacyTests(TestCase):
    def setUp(self):
        apartment = Apartment.objects.create(name="SYN-101")
        self.resident = get_user_model().objects.create_user(
            username="synthetic-resident",
            apartament=apartment,
        )
        self.complaint = Complains.objects.create(
            user=self.resident,
            complain_text="Synthetic complaint about the hallway",
        )
        self.package = Package.objects.create(
            apartament=apartment,
            package_name="Synthetic delivery",
        )
        self.client.force_login(self.resident)

    def test_listings_render_without_writing_resident_data_to_stdout(self):
        for view_name, expected_text in (
            ("complains", self.complaint.complain_text),
            ("packages", self.package.package_name),
        ):
            with self.subTest(view=view_name):
                stdout = StringIO()
                with redirect_stdout(stdout):
                    response = self.client.get(reverse(view_name))

                self.assertContains(response, expected_text)
                for private_value in (
                    self.resident.username,
                    self.resident.apartament.name,
                    self.complaint.complain_text,
                ):
                    self.assertNotIn(private_value, stdout.getvalue())


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
