from django.contrib.auth import get_user_model
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
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


class ComplaintStatusTests(TestCase):
    def test_portal_stores_pending_key_and_displays_label(self):
        user = get_user_model().objects.create_user(username="complaint-resident")
        self.client.force_login(user)
        url = reverse("complains")

        response = self.client.post(url, {"complain": "Broken hallway light"})

        self.assertEqual(response.status_code, 200)
        complaint = Complains.objects.get(user=user)
        self.assertEqual(complaint.status, "PENDING")
        complaint.full_clean()
        self.assertContains(self.client.get(url), "<td>Pending</td>", html=True)


class ComplaintStatusMigrationTests(TransactionTestCase):
    def test_normalizes_only_legacy_pending_status(self):
        previous = [("apartments", "0005_complains_received_at")]
        target = [("apartments", "0006_normalize_complains_status")]
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        self.addCleanup(lambda: MigrationExecutor(connection).migrate(latest))
        old_apps = executor.migrate(previous).apps
        user = old_apps.get_model("apartments", "User").objects.create(
            username="legacy-resident"
        )
        OldComplains = old_apps.get_model("apartments", "Complains")
        expected = {}
        for status in ("Pending", "PENDING", "RESOLVED", "IGNORED"):
            complaint = OldComplains.objects.create(
                user=user, complain_text="Hallway light", status=status
            )
            expected[complaint.pk] = "PENDING" if status == "Pending" else status

        new_apps = MigrationExecutor(connection).migrate(target).apps
        MigratedComplains = new_apps.get_model("apartments", "Complains")
        self.assertEqual(
            dict(MigratedComplains.objects.values_list("pk", "status")), expected
        )
