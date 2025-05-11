from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Ingredient, Recipe, RecipeIngredient,
    Follow, Tag
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("id", "username", "email", "first_name",
    "last_name", "is_staff")
    search_fields = ("email", "username")
    list_filter = ("is_staff", "is_superuser", "is_active")
    empty_value_display = "-пусто-"


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit")
    search_fields = ("name",)
    list_filter = ("measurement_unit",)
    empty_value_display = "-пусто-"


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ("ingredient",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "author",
        "cooking_time",
        "pub_date",
        "count_favorites",
    )
    search_fields = ("name", "author__username", "author__email")
    list_filter = ("author", "name", "pub_date", "tags")
    readonly_fields = ("count_favorites",)
    inlines = [RecipeIngredientInline]
    filter_horizontal = ("tags",)
    empty_value_display = "-пусто-"

    def count_favorites(self, obj):
        return obj.favorited_by.count()

    count_favorites.short_description = "В избранном"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "author", "created_at")
    search_fields = ("user__username", "author__username")
    list_filter = ("created_at",)
    empty_value_display = "-пусто-"
