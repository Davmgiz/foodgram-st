from django.urls import reverse
from rest_framework import viewsets, status, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.core.files.base import ContentFile
import base64
from core.models import (
    User, Ingredient, Recipe,
    RecipeIngredient, Favorite,
    ShoppingCart, Subscription
)
from core.serializers import (
    CustomUserSerializer,
    CustomUserCreateSerializer,
    IngredientSerializer,
    RecipeSerializer,
    SubscriptionRecipeSerializer,
    RecipesUserSerializer
)
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from core.pagination import PageToOffsetPagination
from core.filters import RecipeFilter
import csv
from django.http import HttpResponse
from django.db.models import Sum
from django.core.exceptions import ValidationError


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для управления пользователями."""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            return [AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def set_password(self, request):
        user = request.user
        new_password = request.data.get("new_password")
        current_password = request.data.get("current_password")

        if not user.check_password(current_password):
            return Response({"error": "Неправильный текущий пароль"},
                            status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['put'], url_path='me/avatar',
            permission_classes=[permissions.IsAuthenticated])
    def avatar(self, request):
        user = request.user

        data = request.data.get('avatar')
        if not data:
            raise ValidationError('Вы не передали аватарку')
        try:
            format, str = data.split(';base64,')
        except ValueError:
            raise ValidationError(
                'Недопустимый формат аватарки')
        ext = format.split('/')[-1]
        file = ContentFile(base64.b64decode(str),
                           name=f'avatar{user.id}.{ext}')
        user.avatar = file
        user.save()
        return Response({'avatar': user.avatar.url})

    @avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        user.avatar = 'users/default_avatar.jpg'
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'],
            permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)

        if request.user == author:
            return Response({"error": "Нельзя подписаться на самого себя"},
                            status=status.HTTP_400_BAD_REQUEST)

        _, created = Subscription.objects.get_or_create(user=request.user,
                                                        author=author)
        if not created:
            return Response({"error": "Вы уже подписаны"},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(RecipesUserSerializer(
            author, context={'request': request}
        ).data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        subscription = Subscription.objects.filter(
            user=request.user, author=author
        )

        if not subscription.exists():
            return Response({"error": "Вы не подписаны на него"},
                            status=status.HTTP_400_BAD_REQUEST)

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        queryset = User.objects.filter(authors__user=request.user)
        recipes_limit = request.query_params.get('recipes_limit')
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = RecipesUserSerializer(
                page, many=True, context={'request': request,
                                          'recipes_limit': recipes_limit}
            )
            return self.get_paginated_response(serializer.data)

        serializer = RecipesUserSerializer(
            queryset, many=True, context={'request': request,
                                          'recipes_limit': recipes_limit}
        )
        return Response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для управления рецептами."""

    queryset = Recipe.objects.all().order_by('-date_published')
    serializer_class = RecipeSerializer
    pagination_class = PageToOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'get_link']:
            return [permissions.AllowAny()]
        else:
            return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        user = self.request.user
        if serializer.instance.author == user:
            serializer.save()
        else:
            return Response({'error': 'Вы не являетесь автором'},
                            status=status.HTTP_403_FORBIDDEN)

    def perform_destroy(self, instance):
        if instance.author == self.request.user:
            instance.delete()
        else:
            return Response({'error': 'Вы не являетесь автором'},
                            status=status.HTTP_403_FORBIDDEN)

    @staticmethod
    def handle_recipe(model, user, recipe, add=True):
        if add:
            obj, created = model.objects.get_or_create(
                user=user, recipe=recipe
            )
            if not created:
                return Response({'error': 'Рецепт уже добавлен'},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response(SubscriptionRecipeSerializer(recipe).data,
                            status=status.HTTP_201_CREATED)

        obj = model.objects.filter(user=user, recipe=recipe)
        if not obj.exists():
            return Response({'error': 'Рецепт не найден'},
                            status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        return self.handle_recipe(Favorite, request.user, recipe, True)

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        return self.handle_recipe(Favorite, request.user, recipe, False)

    @action(detail=True, methods=['post'],
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        return self.handle_recipe(ShoppingCart, request.user, recipe, True)

    @shopping_cart.mapping.delete
    def remove_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        return self.handle_recipe(ShoppingCart, request.user, recipe, False)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Скачивание списка покупок в формате CSV."""

        ingredients = RecipeIngredient.objects.filter(
            recipe__in=ShoppingCart.objects.filter(
                user=request.user
            ).values('recipe')

        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount')).order_by('ingredient__name')

        if not ingredients:
            return Response({'error': 'Корзина пуста'},
                            status=status.HTTP_400_BAD_REQUEST)

        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = ('attachment; filename='
                                           '"shopping_cart.csv"')

        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Ингредиент', 'Количество', 'Единица измерения'])

        for item in ingredients:
            writer.writerow([
                item['ingredient__name'].capitalize(),
                item['total_amount'],
                item['ingredient__measurement_unit']
            ])

        return response

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        """Генерация короткой ссылки на рецепт."""
        recipe = self.get_object()
        short_url = request.build_absolute_uri(
            reverse('recipe_redirect', args=[recipe.pk])
        )
        return Response({'short-link': short_url}, status=status.HTTP_200_OK)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для управления ингридиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    search_fields = ('^name',)

    def get_queryset(self):
        queryset = Ingredient.objects.all().order_by('name')
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset
