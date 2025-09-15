from django.db import migrations

def create_superuser(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    # Admin 1
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='141020023sd'
        )
    # Admin 2
    if not User.objects.filter(username='admin2').exists():
        User.objects.create_superuser(
            username='admin2',
            email='admin2@example.com',
            password='admin2pass'
        )
    # Admin 3
    if not User.objects.filter(username='admin3').exists():
        User.objects.create_superuser(
            username='admin3',
            email='admin3@example.com',
            password='admin3pass'
        )
    # Admin 4
    if not User.objects.filter(username='admin4').exists():
        User.objects.create_superuser(
            username='admin4',
            email='admin4@example.com',
            password='admin4pass'
        )

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),  # Change to your latest migration if needed
    ]

    operations = [
        migrations.RunPython(create_superuser),
    ]