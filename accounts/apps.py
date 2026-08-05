from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_default_superuser(sender, **kwargs):
    import os
    from django.contrib.auth import get_user_model

    User = get_user_model()
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@devlink.com')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin12345')

    if not User.objects.filter(is_superuser=True).exists():
        try:
            print(f"Creating default superuser '{username}'...")
            User.objects.create_superuser(username=username, email=email, password=password)
            print(f"Superuser '{username}' created successfully!")
        except Exception as e:
            print(f"Superuser creation skipped: {e}")


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'Accounts'

    def ready(self):
        import accounts.signals  # noqa: F401
        post_migrate.connect(create_default_superuser, sender=self)
