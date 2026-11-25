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


class PrivatePortalViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        apartment = Apartment.objects.create(name="101")
        other_apartment = Apartment.objects.create(name="102")
        cls.resident = get_user_model().objects.create_user(
            username="resident", apartament=apartment,
        )
        neighbor = get_user_model().objects.create_user(
            username="neighbor", apartament=apartment,
        )
        cls.package = Package.objects.create(
            apartament=apartment, package_name="Resident package",
        )
        Package.objects.create(
            apartament=other_apartment, package_name="Other package",
        )
        cls.complaint = Complains.objects.create(
            user=cls.resident, complain_text="Resident complaint",
        )
        Complains.objects.create(
            user=neighbor, complain_text="Neighbor complaint",
        )

    def test_anonymous_packages_redirects_to_login(self):
        self.assert_login_redirect("packages")

    def test_anonymous_complains_redirects_to_login(self):
        self.assert_login_redirect("complains")

    def assert_login_redirect(self, route_name):
        path = reverse(route_name)
        self.assertRedirects(
            self.client.get(path),
            f"{reverse('login')}?next={path}",
            fetch_redirect_response=False,
        )

    def test_packages_are_filtered_by_apartment(self):
        self.client.force_login(self.resident)

        response = self.client.get(reverse("packages"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["packages"]), [self.package])

    def test_complaints_are_filtered_by_author_within_apartment(self):
        self.client.force_login(self.resident)

        response = self.client.get(reverse("complains"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["complains"]), [self.complaint])
