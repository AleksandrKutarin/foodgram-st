from django.shortcuts import get_object_or_404
from rest_framework import (
    viewsets,
    permissions,
    filters as drf_filters,
    status
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import (
    Ingredient,
    Recipe,
    Tag,
    RecipeIngredient,
    User,
    Follow,
)
from .serializers import (
    IngredientSerializer,
    RecipeSerializer,
    TagSerializer,
    RecipeMinifiedSerializer,
    UserWithRecipesSerializer,
    UserAvatarSerializer,
)
from .filters import RecipeFilter, IngredientNameFilter
from django.http import HttpResponse
from django.db.models import Sum
from djoser.views import UserViewSet as DjoserUserViewSet
from .pagination import CustomPageNumberPagination
from .permissions import IsAuthorOrReadOnly


class IngredientViewSet(
    viewsets.ReadOnlyModelViewSet
):
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = (
        None
    )

    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientNameFilter

    def get_queryset(self):
        return Ingredient.objects.all()


class TagViewSet(
    viewsets.ReadOnlyModelViewSet
):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [
        IsAuthorOrReadOnly
    ]

    filter_backends = (
        DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter,
    )
    filterset_class = RecipeFilter
    search_fields = ("name", "text")
    ordering_fields = ("pub_date", "name")

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == "POST":
            if recipe.favorited_by.filter(id=user.id).exists():
                return Response(
                    {"errors": "Рецепт уже в избранном"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            recipe.favorited_by.add(user)
            serializer = RecipeMinifiedSerializer(
                recipe
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            if not recipe.favorited_by.filter(id=user.id).exists():
                return Response(
                    {"errors": "Рецепта нет в избранном"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            recipe.favorited_by.remove(user)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == "POST":
            if recipe.in_shopping_cart_for_users.filter(id=user.id).exists():
                return Response(
                    {"errors": "Рецепт уже в списке покупок"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            recipe.in_shopping_cart_for_users.add(user)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            print(
                f"[DEBUG] Attempting to remove recipe {pk} \
                from shopping cart for user {user.id} ({user.username})"
            )
            recipe_in_cart = recipe.in_shopping_cart_for_users.filter(
                id=user.id
            ).exists()
            print(f"[DEBUG] Recipe in cart for user? {recipe_in_cart}")

            if not recipe_in_cart:
                print(
                    f"[DEBUG] Condition ({not recipe_in_cart}) is True. \
                    Recipe not in cart or user mismatch."
                )
                return Response(
                    {"errors": "Рецепта нет в списке покупок"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            print(
                f"[DEBUG] Attempting recipe. \
                in_shopping_cart_for_users.remove({user})"
            )
            try:
                recipe.in_shopping_cart_for_users.remove(user)
                print(
                    f"[DEBUG] recipe.in_shopping_cart_for_users. \
                    remove({user}) EXECUTED successfully."
                )
            except Exception as e:
                print(f"[DEBUG] EXCEPTION during .remove(user): {str(e)}")
                return Response(
                    {"errors": f"Ошибка при удалении: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=["get"], permission_classes=[
            permissions.IsAuthenticated
        ]
    )
    def download_shopping_cart(self, request):
        user = request.user
        shopping_list_items = (
            RecipeIngredient.objects.filter(
                recipe__in_shopping_cart_for_users=user
            )
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
            .order_by("ingredient__name")
        )

        if not shopping_list_items:
            return Response(
                {"detail": "Список покупок пуст."},
                status=status.HTTP_404_NOT_FOUND
            )

        content = []
        content.append(
            f'''Список покупок для пользователя:
            {user.get_full_name() or user.username}\n'''
        )
        content.append("--------------------------------------------------\n")
        for item in shopping_list_items:
            content.append(
                f'''- {item['ingredient__name']}
                ({item['ingredient__measurement_unit']})
                - {item['total_amount']}\n'''
            )
        content.append("--------------------------------------------------\n")
        content.append(
            f'Foodgram, {request.build_absolute_uri("/")[:-1]}\n'
        )

        response_content = "".join(content)
        response = HttpResponse(
            response_content, content_type="text/plain; charset=utf-8"
        )
        response[
            "Content-Disposition"
        ] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[
            permissions.AllowAny
        ],
        url_path="get-link",
        url_name="recipe-get-link",
    )
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link_url = request.build_absolute_uri(
            f"/s/{recipe.id}/"
        )
        return Response(
            {"short-link": short_link_url},
            status=status.HTTP_200_OK
        )


class CustomUserViewSet(DjoserUserViewSet):
    print(
        '''\n\nDEBUG: CustomUserViewSet CLASS DEFINITION
        IS BEING READ BY PYTHON INTERPRETER\n\n'''
    )

    def __init__(self, *args, **kwargs):
        print(
            '''\n\nDEBUG: CustomUserViewSet INSTANCE
            IS BEING INITIALIZED! (e.g., by router)\n\n'''
        )
        super().__init__(*args, **kwargs)

    pagination_class = CustomPageNumberPagination

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.permission_classes = [permissions.AllowAny]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    @action(
        detail=False, methods=["get"],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        """Возвращает пользователей,
        на которых подписан текущий пользователь."""
        user = request.user
        followed_authors = User.objects.filter(following__user=user)

        page = self.paginate_queryset(followed_authors)
        if page is not None:
            serializer = UserWithRecipesSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserWithRecipesSerializer(
            followed_authors, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        """Подписаться или отписаться от пользователя."""
        author_to_follow = get_object_or_404(User, id=id)
        current_user = request.user

        if current_user == author_to_follow:
            return Response(
                {"errors": "Нельзя подписаться на самого себя"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == "POST":
            if Follow.objects.filter(
                user=current_user, author=author_to_follow
            ).exists():
                return Response(
                    {"errors": "Вы уже подписаны на этого пользователя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Follow.objects.create(user=current_user, author=author_to_follow)
            serializer = UserWithRecipesSerializer(
                author_to_follow, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            subscription = Follow.objects.filter(
                user=current_user, author=author_to_follow
            )
            if not subscription.exists():
                return Response(
                    {"errors": "Вы не были подписаны на этого пользователя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["put", "delete"],
        permission_classes=[permissions.IsAuthenticated],
        serializer_class=UserAvatarSerializer,
        url_path="me/avatar",
        url_name="user-me-avatar",
    )
    def avatar(self, request):
        user = request.user
        if request.method == "PUT":
            serializer = self.get_serializer(user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        elif request.method == "DELETE":
            if user.avatar:
                user.avatar.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"detail": "Аватар не найден."},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
