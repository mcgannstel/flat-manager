import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create an initial superuser from environment variables if it doesn't already exist."

    def handle(self, *args, **options):
        if os.environ.get("CREATE_SUPERUSER", "False") != "True":
            self.stdout.write("CREATE_SUPERUSER is not True; skipping.")
            return

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not username or not password:
            self.stdout.write("Missing superuser env vars; skipping.")
            return

        User = get_user_model()

        if User.objects.filter(username=username).exists():
            self.stdout.write(f"Superuser '{username}' already exists; skipping.")
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        self.stdout.write(f"Superuser '{username}' created.")