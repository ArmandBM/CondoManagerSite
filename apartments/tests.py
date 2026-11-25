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


class ComplaintViewTests(TestCase):
    def test_new_complaint_stores_pending_key_and_shows_label(self):
        user = get_user_model().objects.create_user(username="complaint-resident")
        self.client.force_login(user)

        response = self.client.post(
            reverse("complains"),
            {"complain": "The hallway light is out."},
        )

        complaint = Complains.objects.get(user=user)
        self.assertEqual(complaint.status, "PENDING")
        self.assertContains(response, "<td>Pending</td>", html=True)


class ComplaintStatusMigrationTests(TransactionTestCase):
    def test_migration_normalizes_only_legacy_pending_status(self):
        previous = [("apartments", "0005_complains_received_at")]
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        self.addCleanup(self.restore_migrations, latest)
        executor.migrate(previous)

        old_apps = executor.loader.project_state(previous).apps
        user = old_apps.get_model("apartments", "User").objects.create(
            username="migration-resident",
        )
        complaints = old_apps.get_model("apartments", "Complains").objects
        expected_statuses = {}
        for status in ("Pending", "PENDING", "RESOLVED", "IGNORED", "Unknown"):
            complaint = complaints.create(user=user, complain_text="Test complaint", status=status)
            expected_statuses[complaint.pk] = "PENDING" if status == "Pending" else status

        MigrationExecutor(connection).migrate(latest)

        actual_statuses = dict(Complains.objects.values_list("pk", "status"))
        self.assertEqual(actual_statuses, expected_statuses)

    def restore_migrations(self, targets):
        MigrationExecutor(connection).migrate(targets)
