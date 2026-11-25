from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Apartment, Complains, Package


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


class ResidentViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        apartment = Apartment.objects.create(name="101")
        cls.other_apartment = Apartment.objects.create(name="102")
        cls.resident = get_user_model().objects.create_user(
            username="first-resident", apartament=apartment
        )
        cls.neighbor = get_user_model().objects.create_user(
            username="second-resident", apartament=apartment
        )

    def test_anonymous_requests_redirect_to_login_with_next(self):
        for route, method in (
            ("packages", self.client.get),
            ("complains", self.client.get),
            ("complains", self.client.post),
        ):
            with self.subTest(route=route, method=method.__name__):
                url = reverse(route)
                self.assertRedirects(method(url), f"{reverse('login')}?next={url}")

    def test_packages_are_scoped_to_the_residents_apartment(self):
        package = Package.objects.create(
            apartament=self.resident.apartament, package_name="Local package"
        )
        Package.objects.create(
            apartament=self.other_apartment, package_name="Other package"
        )

        for resident in (self.resident, self.neighbor):
            with self.subTest(resident=resident.username):
                self.client.force_login(resident)
                response = self.client.get(reverse("packages"))
                self.assertEqual(list(response.context["packages"]), [package])

    def test_complaints_are_scoped_to_the_author_within_an_apartment(self):
        for resident in (self.resident, self.neighbor):
            Complains.objects.create(user=resident, complain_text=resident.username)

        for resident in (self.resident, self.neighbor):
            with self.subTest(resident=resident.username):
                self.client.force_login(resident)
                response = self.client.get(reverse("complains"))
                self.assertEqual(
                    [complaint.user_id for complaint in response.context["complains"]],
                    [resident.pk],
                )
