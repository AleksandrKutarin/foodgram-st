from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
    CustomUserViewSet,
)

app_name = "api"

router_api = DefaultRouter()
router_api.register(r"ingredients", IngredientViewSet, basename="ingredients")
router_api.register(r"tags", TagViewSet, basename="tags")
router_api.register(r"recipes", RecipeViewSet, basename="recipes")
router_api.register(r"users", CustomUserViewSet, basename="users")

urlpatterns = [
    path("", include(router_api.urls)),
]
