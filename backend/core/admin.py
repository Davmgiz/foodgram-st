from django.contrib import admin
from .models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart,
    Subscription,
    User
)


# Кастомная админка для User
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_active')


# Инлайн-редактирование ингредиентов в рецепте
class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1  # Добавляет одну пустую строку для добавления нового ингредиента
    autocomplete_fields = ('ingredient',)  # Автозаполнение для ингредиентов


# Кастомная админка для модели Recipe
@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'cooking_time', 'date_published', 'favorites_count')
    list_filter = ('author', 'cooking_time', 'date_published')
    search_fields = ('name', 'author__username')
    inlines = [RecipeIngredientInline]  # Добавляем инлайн-редактирование ингредиентов

    # Метод для подсчёта количества добавлений в избранное
    def favorites_count(self, obj):
        return obj.favorited_by_users.count()
    favorites_count.short_description = 'Добавлено в избранное'  # type: ignore


# Кастомная админка для модели Ingredient
@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    ordering = ('name',)


# Кастомная админка для модели RecipeIngredient
@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    list_filter = ('recipe', 'ingredient')
    search_fields = ('recipe__name', 'ingredient__name')


# Кастомная админка для модели Favorite
@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


# Кастомная админка для модели Subscription
@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    list_filter = ('user', 'author')
    search_fields = ('user__username', 'author__username')


# Кастомная админка для модели ShoppingCart
@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
