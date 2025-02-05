from rest_framework import serializers
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from core.models import (
    Ingredient, Recipe, RecipeIngredient,
    Favorite, ShoppingCart, User, Subscription
)


class UserProfileSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'avatar', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, author=obj
            ).exists()
        return False


class RecipesUserSerializer(UserProfileSerializer):    
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count',
                                             read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit', 10**10)
        recipes = obj.recipes.all()[:int(recipes_limit)]
        return SubscriptionRecipeSerializer(recipes, many=True,
                                            context=self.context).data


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.CharField(source='ingredient.name', read_only=True)
    amount = serializers.IntegerField(min_value=1)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients', many=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField(min_value=1)
    image = Base64ImageField(allow_null=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    @staticmethod
    def rec_save(recipe, data):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient.get('amount')
            ) for ingredient in data
        ])

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients')
        recipe = super().create(validated_data)
        self.rec_save(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients', None)
        validated_ingredients = self.validate_ingredients(ingredients_data)
        instance.recipe_ingredients.all().delete()
        self.rec_save(instance, validated_ingredients)
        return super().update(instance, validated_data)

    def get_is_in_shopping_cart(self, recipe):
        user = self.context['request'].user
        return user.is_authenticated and ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).exists()

    def get_is_favorited(self, recipe):
        user = self.context['request'].user
        return user.is_authenticated and Favorite.objects.filter(
            user=user, recipe=recipe
        ).exists()

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError('Нет ингредиентов')
        seen = set()
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            if ingredient_id in seen:
                raise serializers.ValidationError('Ингредиенты повторяются.')
            seen.add(ingredient_id)

        return ingredients

    def validate_image(self, image):
        if not image:
            raise serializers.ValidationError('Нет изображения')
        return image


class SubscriptionRecipeSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields
