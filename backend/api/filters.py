from rest_framework import filters
import django_filters
from .models import (
    Recipe,
    Tag,
    Ingredient,
)


class IngredientSearchFilter(filters.SearchFilter):
    """
    Custom search filter for ingredients to use
    'name' as the query parameter
    for searching, as defined in the OpenAPI schema.
    """

    search_param = "name"

class IngredientNameFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name",
    lookup_expr="startswith")

    class Meta:
        model = Ingredient
        fields = ["name"]


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all(),
        label="Filter by tag slugs",
    )
    author = django_filters.NumberFilter(field_name="author__id")

    is_favorited = django_filters.CharFilter(
        method="filter_is_favorited_custom"
        )
    is_in_shopping_cart = django_filters.CharFilter(
        method="filter_is_in_shopping_cart_custom"
    )

    class Meta:
        model = Recipe
        fields = ["author", "tags", "is_favorited", "is_in_shopping_cart"]

    def filter_is_favorited_custom(self, queryset, name, value):
        print(
            f'''[DEBUG CUSTOM_FAVORITED_FILTER] User: {getattr
            (self.request, 'user', 'None')
            },
            Param value: '{value}' (type: {type(value)})'''
        )

        user = getattr(self.request, "user", None)

        if value == "1":
            if user and user.is_authenticated:
                return queryset.filter(favorited_by=user)
            else:
                return queryset.none()
        elif value == "0":
            if user and user.is_authenticated:
                return queryset.exclude(favorited_by=user)
            else:
                return queryset

        return queryset

    def filter_is_in_shopping_cart_custom(self, queryset, name, value):
        print(
            f'''[DEBUG CUSTOM_SHOP_CART_FILTER] User: {getattr
            (self.request, 'user', 'None')
            }, Param value: '{value}' (type: {type(value)})'''
        )  # Отладка
        user = getattr(self.request, "user", None)

        if value == "1":
            if user and user.is_authenticated:
                return queryset.filter(in_shopping_cart_for_users=user)
            else:
                return queryset.none()
        elif value == "0":
            if user and user.is_authenticated:
                return queryset.exclude(in_shopping_cart_for_users=user)
            else:
                return queryset
        return queryset
