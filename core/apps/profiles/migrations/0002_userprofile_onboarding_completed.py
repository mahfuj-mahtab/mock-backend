from django.db import migrations, models


def mark_existing_profiles_onboarding_completed(apps, schema_editor):
    UserProfile = apps.get_model("profiles", "UserProfile")
    UserProfile.objects.all().update(onboarding_completed=True)


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="onboarding_completed",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(
            mark_existing_profiles_onboarding_completed,
            migrations.RunPython.noop,
        ),
    ]
