import random

from django.db import migrations, models


def assign_user_ids(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    random_generator = random.SystemRandom()
    used_codes = set(
        User.objects.exclude(user_id__isnull=True)
        .exclude(user_id="")
        .values_list("user_id", flat=True)
    )

    for user in User.objects.filter(user_id__isnull=True):
        for _ in range(100):
            code = str(random_generator.randint(10000, 99999))
            if code not in used_codes:
                used_codes.add(code)
                user.user_id = code
                user.save(update_fields=["user_id"])
                break
        else:
            raise RuntimeError("Unable to generate a unique user ID.")


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="user_id",
            field=models.CharField(blank=True, editable=False, max_length=5, null=True, unique=True),
        ),
        migrations.RunPython(assign_user_ids, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="user",
            name="user_id",
            field=models.CharField(editable=False, max_length=5, unique=True),
        ),
    ]
