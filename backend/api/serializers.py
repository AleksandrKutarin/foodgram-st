from rest_framework import serializers
from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from django.contrib.auth.validators import (
    UnicodeUsernameValidator,
)
from rest_framework.validators import (
    UniqueValidator,
)
from .models import (
    Ingredient,
    Recipe,
    Tag,
    RecipeIngredient,
    User,
    Follow,
)
from django.core.validators import (
    MinValueValidator,
)

class CustomUserCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        validators=[
            UnicodeUsernameValidator(),
            UniqueValidator(
                queryset=User.objects.all(),
                message="Пользователь с таким именем уже существует.",
            ),
        ],
        max_length=150,
    )

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "password",
            "first_name",
            "last_name",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "id": {"read_only": True},
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class CustomUserSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(read_only=True,
    required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated and isinstance(obj,
        User):
            return Follow.objects.filter(user=request.user,
            author=obj).exists()
        return False

    def to_representation(self, instance):
        if not isinstance(instance, User):
            return {
                "id": None,
                "email": "",
                "username": "Anonymous",
                "first_name": "",
                "last_name": "",
                "is_subscribed": False,
                "avatar": None,
            }
        return super().to_representation(instance)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
        )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeIngredientWriteSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        min_value=1
    )


class IngredientSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(
        validators=[
            MinValueValidator(
                1,
                message="Время приготовления должно быть не меньше 1 минуты."
            )
        ],
        required=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        required=False,
        allow_empty=True,
        source="tags_for_processing",
    )
    ingredients = RecipeIngredientWriteSerializer(
        many=True, write_only=True, source="ingredients_for_processing"
    )

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
            "tags",
            "ingredients",
        )

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            return obj.favorited_by.filter(id=user.id).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            return obj.in_shopping_cart_for_users.filter(id=user.id).exists()
        return False

    def to_representation(self, instance):
        """Готовим данные для вывода (JSON ответа),
        чтобы соответствовать RecipeList."""
        representation = super().to_representation(
            instance
        )
        representation["ingredients"] = RecipeIngredientReadSerializer(
            instance.recipe_ingredients.all(),
            many=True,
            context=self.context,
        ).data

        representation.pop(
            "tags_for_processing", None
        )
        representation.pop("ingredients_for_processing", None)

        return representation

    def validate(self, data):

        print(f"[DEBUG VALIDATE - initial_data] {self.initial_data}")
        print(f"[DEBUG VALIDATE - data_before_custom_checks] {data}")

        image_initial_value = self.initial_data.get("image")
        if "image" in self.initial_data and (
            image_initial_value is None
            or (
                isinstance(image_initial_value, str)
                and not image_initial_value.strip()
            )
        ):
            print(
                '''[DEBUG VALIDATE] Image is empty
                in initial_data, raising ValidationError.'''
            )
            raise serializers.ValidationError(
                {"image": "Поле image не может быть пустым."}
            )
        ingredients_value = data.get("ingredients_for_processing")
        print(
            f'''[DEBUG VALIDATE] Ingredients value from data:
            {ingredients_value}'''
        )
        if ingredients_value is None:
            print(
                '''[DEBUG VALIDATE] Ingredients key
                missing or None, raising ValidationError.'''
            )
            pass

        if not ingredients_value:
            print(
                '''[DEBUG VALIDATE] Empty ingredients list,
                raising ValidationError.'''
            )
            raise serializers.ValidationError(
                {"ingredients": "Нужно указать хотя бы один ингредиент."}
            )

        ingredient_ids = []
        try:
            for item in ingredients_value:
                if not isinstance(item.get("id"), Ingredient):
                    print(
                        f'''[DEBUG VALIDATE] Invalid item ID type:
                        {type(item.get('id'))} for item {item}'''
                    )
                    raise serializers.ValidationError(
                        {"ingredients": "Некорректный формат ID ингредиента."}
                    )
                ingredient_ids.append(item["id"].id)
        except Exception as e:
            print(f"[DEBUG VALIDATE] Error processing item IDs: {e}")
            raise serializers.ValidationError(
                {"ingredients": f"Ошибка обработки ID ингредиентов: {e}"}
            )

        print(f"[DEBUG VALIDATE] Collected ingredient IDs: {ingredient_ids}")
        if len(ingredient_ids) != len(set(ingredient_ids)):
            print(
                '''[DEBUG VALIDATE] Duplicate ingredients found,
                 raising ValidationError.'''
            )
            raise serializers.ValidationError(
                {"ingredients": "Ингредиенты не должны повторяться."}
            )

        tags_value = data.get("tags_for_processing")
        print(f"[DEBUG VALIDATE] Tags value from data: {tags_value}")
        if tags_value is not None and not tags_value:
            print(
                '''[DEBUG VALIDATE] Empty tags list (but key exists),
                 raising ValidationError.'''
            )
            raise serializers.ValidationError(
                {"tags": "Если теги указаны, список не должен быть пустым."}
            )

        print(f"[DEBUG VALIDATE - data_after_custom_checks] {data}")
        return data

    @transaction.atomic
    def create(self, validated_data):
        print(
            f'''[DEBUG CREATE RECIPE] Validated data BEFORE POP:
            {validated_data}'''
        )
        ingredients_list_data = validated_data.pop
        ("ingredients_for_processing")
        tags_list_data = validated_data.pop("tags_for_processing", None)
        print(
            f"[DEBUG CREATE RECIPE] Ingredients data: {ingredients_list_data}"
        )
        print(f"[DEBUG CREATE RECIPE] Tags data: {tags_list_data}")
        print(
            f"[DEBUG CREATE RECIPE] Remaining validated data: {validated_data}"
        )

        validated_data["author"] = self.context["request"].user
        recipe = Recipe.objects.create(**validated_data)

        recipe_ingredients_to_create = []
        for item_data in ingredients_list_data:
            recipe_ingredients_to_create.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=item_data["id"],
                    amount=item_data["amount"],
                )
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients_to_create)

        if tags_list_data:
            recipe.tags.set(tags_list_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_list_data = validated_data.pop
        ("ingredients_for_processing", None)
        tags_list_data = validated_data.pop("tags_for_processing", None)

        instance.name = validated_data.get("name", instance.name)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )

        if "image" in validated_data:
            instance.image = validated_data["image"]

        instance.save()

        if ingredients_list_data is not None:
            RecipeIngredient.objects.filter(recipe=instance).delete()
            recipe_ingredients_to_create = []
            for item_data in ingredients_list_data:
                recipe_ingredients_to_create.append(
                    RecipeIngredient(
                        recipe=instance,
                        ingredient=item_data["id"],
                        amount=item_data["amount"],
                    )
                )
            RecipeIngredient.objects.bulk_create(recipe_ingredients_to_create)

        if (
            tags_list_data is not None
        ):
            instance.tags.set(tags_list_data)
        elif (
            "tags" in self.initial_data and tags_list_data is None
        ):
            instance.tags.clear()

        return instance


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """
    Минимальный сериализатор для рецептов, используемый при добавлении
    в избранное или список покупок.
    """

    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = ("id", "name", "image", "cooking_time")


class UserWithRecipesSerializer(serializers.ModelSerializer):
    """
    Сериализатор для пользователя с его рецептами (минимальный набор)
    и статусом подписки текущего пользователя на него.
    Используется для отображения подписок.
    """

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.ImageField(
        read_only=True, required=False, allow_null=True
    )

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )
        read_only_fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Follow.objects.filter(
                user=request.user, author=obj
                ).exists()
        return False

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes_limit_str = (
            request.query_params.get("recipes_limit")
            if request else None
        )
        queryset = obj.recipes.all()
        if recipes_limit_str:
            try:
                recipes_limit = int(recipes_limit_str)
                if recipes_limit > 0:
                    queryset = queryset[:recipes_limit]
            except ValueError:
                pass
        return RecipeMinifiedSerializer(
            queryset, many=True, context=self.context
            ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()



class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(
        required=True
    )

    class Meta:
        model = User
        fields = ("avatar",)
