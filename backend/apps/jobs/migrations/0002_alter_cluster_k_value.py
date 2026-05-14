from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cluster",
            name="k_value",
            field=models.IntegerField(),
        ),
    ]
