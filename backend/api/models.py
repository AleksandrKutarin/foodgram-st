from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import MinValueValidator
from django.db import models


class User(AbstractUser):
    # Custom user model for Foodgram
    email = models.EmailField(
        verbose_name="Адрес электронной почты", max_length=254, unique=True
    )
    username = models.CharField(
        verbose_name="Уникальный юзернейм",
        max_length=150,
        unique=True,
    )
    first_name = models.CharField(verbose_name="Имя", max_length=150)
    last_name = models.CharField(verbose_name="Фамилия", max_length=150)
    avatar = models.ImageField(
        verbose_name="Аватар", upload_to="users/avatars/",
        null=True, blank=True
    )

    groups = models.ManyToManyField(
        Group,
        verbose_name="groups",
        blank=True,
        help_text=(
            '''The groups this user belongs to.
            A user will get all permissions '''
            "granted to each of their groups."
        ),
        related_name="api_user_groups",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name="user permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        related_name="api_user_permissions",
        related_query_name="user",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["username"]

    def __str__(self):
        return self.username


class Ingredient(models.Model):
    name = models.CharField(verbose_name="Название ингредиента",
    max_length=128)
    measurement_unit = models.CharField(verbose_name="Единица измерения",
    max_length=64)

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="unique_ingredient_measure"
            )
        ]

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Tag(models.Model):
    name = models.CharField(verbose_name="Название тега",
    max_length=50, unique=True)
    color = models.CharField(
        verbose_name="Цвет в HEX",
        max_length=7,
        unique=True,
        validators=[],
    )
    slug = models.SlugField(verbose_name="Слаг", max_length=50, unique=True)

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор рецепта",
    )
    name = models.CharField(verbose_name="Название рецепта", max_length=128)
    image = models.ImageField(
        verbose_name="Изображение",
        upload_to="recipes/images/",
    )
    text = models.TextField(verbose_name="Описание рецепта")
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        related_name="recipes",
        verbose_name="Ингредиенты",
    )
    tags = models.ManyToManyField(Tag, related_name="recipes",
    verbose_name="Теги")
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления (в минутах)",
        validators=[],
    )
    pub_date = models.DateTimeField(verbose_name="Дата публикации",
    auto_now_add=True)
    favorited_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="favorite_recipes",
        verbose_name="Кто добавил в избранное",
        blank=True,
    )
    in_shopping_cart_for_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="shopping_cart_recipes",
        verbose_name="Кто добавил в список покупок",
        blank=True,
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ["-pub_date"]

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name="ingredient_recipes",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveIntegerField(
        verbose_name="Количество", validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient"
            )
        ]

    def __str__(self):
        return f'''{self.ingredient.name}
        ({self.amount} {self.ingredient.measurement_unit})
        in "{self.recipe.name}"'''


class Follow(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор, на которого подписаны",
    )
    created_at = models.DateTimeField(auto_now_add=True,
    verbose_name="Дата подписки")

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "author"],
            name="unique_follow"),
            models.CheckConstraint(
                check=~models.Q(user=models.F("author")),
                name="prevent_self_follow"
            ),
        ]

    def __str__(self):
        return f"{self.user} follows {self.author}"
