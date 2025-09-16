from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Create up to 4 superusers from environment variables'

    def handle(self, *args, **options):
        User = get_user_model()
        admins = os.getenv('DJANGO_SUPERUSER_ADMINS')

        if not admins:
            self.stdout.write(self.style.ERROR('No admin accounts configured. Please set DJANGO_SUPERUSER_ADMINS.'))
            return

        admin_list = admins.split(';')

        if len(admin_list) > 4:
            self.stdout.write(self.style.ERROR('You can create a maximum of 4 admin accounts.'))
            return

        for admin_str in admin_list:
            try:
                username, email, password = admin_str.split(',')
                if not User.objects.filter(username=username).exists():
                    self.stdout.write(self.style.SUCCESS(f'Creating superuser: {username}'))
                    User.objects.create_superuser(username=username, email=email, password=password)
                else:
                    self.stdout.write(self.style.WARNING(f'Superuser {username} already exists.'))
            except ValueError:
                self.stdout.write(self.style.ERROR(f'Invalid admin format: {admin_str}'))