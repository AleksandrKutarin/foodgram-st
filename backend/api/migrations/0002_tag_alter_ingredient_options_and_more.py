from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Tag",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=50, unique=True,
                        verbose_name="Название тега"
                    ),
                ),
                (
                    "color",
                    models.CharField(
                        max_length=7, unique=True,
                        verbose_name="Цвет в HEX"
                    ),
                ),
                ("slug", models.SlugField(unique=True,
                verbose_name="Слаг")),
            ],
            options={
                "verbose_name": "Тег",
                "verbose_name_plural": "Теги",
                "ordering": ("name",),
            },
        ),
        migrations.AlterModelOptions(
            name="ingredient",
            options={
                "ordering": ("name",),
                "verbose_name": "Ингредиент",
                "verbose_name_plural": "Ингредиенты",
            },
        ),
        migrations.AlterField(
            model_name="recipe",
            name="cooking_time",
            field=models.PositiveSmallIntegerField(
                verbose_name="Время приготовления (в минутах)"
            ),
        ),
        migrations.AlterField(
            model_name="recipe",
            name="image",
            field=models.ImageField(
                upload_to="recipes/images/", verbose_name="Изображение"
            ),
        ),
        migrations.AlterField(
            model_name="recipe",
            name="name",
            field=models.CharField(max_length=128,
            verbose_name="Название рецепта"),
        ),
        migrations.AddField(
            model_name="recipe",
            name="tags",
            field=models.ManyToManyField(
                related_name="recipes", to="api.tag", verbose_name="Теги"
            ),
        ),
    ]
